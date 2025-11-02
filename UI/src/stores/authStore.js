// src/stores/authStore.js
// Ce fichier gère tout ce qui concerne l'authentification (connexion, déconnexion, etc.)

import { defineStore } from 'pinia'
import { supabase } from '../lib/supabaseClient'

export const useAuthStore = defineStore('auth', {
  state: () => ({
    // L'utilisateur actuellement connecté (null si personne n'est connecté)
    user: null,
    // Si on est en train de charger les infos de l'utilisateur
    loading: false,
    // Message d'erreur s'il y en a un
    error: null,
    // ⏰ Timer pour l'auto-logout
    inactivityTimer: null,
    // ⏰ Durée d'inactivité avant déconnexion (en millisecondes) - 15 minutes
    inactivityTimeout: 15 * 60 * 1000 // 15 minutes = 900000ms
  }),

  getters: {
    // Est-ce que quelqu'un est connecté ?
    isAuthenticated: (state) => state.user !== null,
    
    // Récupérer l'email de l'utilisateur connecté
    userEmail: (state) => state.user?.email || '',
    
    // Récupérer l'ID de l'utilisateur connecté
    userId: (state) => state.user?.id || null
  },

  actions: {
    // ⏰ DÉMARRER le timer d'inactivité
    // Cette fonction va déconnecter l'utilisateur après 15 minutes sans activité
    startInactivityTimer() {
      // D'abord, on efface le timer existant (si il y en a un)
      this.clearInactivityTimer()
      
      console.log('⏰ Timer d\'inactivité démarré (15 minutes)')
      
      // On créé un nouveau timer qui va déconnecter après 15 minutes
      this.inactivityTimer = setTimeout(() => {
        console.log('⏰ 15 minutes d\'inactivité détectées - Déconnexion automatique')
        this.autoLogout()
      }, this.inactivityTimeout)
    },

    // ⏰ RÉINITIALISER le timer d'inactivité
    // À chaque fois que l'utilisateur fait quelque chose, on remet le compteur à zéro
    resetInactivityTimer() {
      // Si l'utilisateur est connecté, on redémarre le timer
      if (this.user) {
        this.startInactivityTimer()
      }
    },

    // ⏰ ARRÊTER le timer d'inactivité
    clearInactivityTimer() {
      if (this.inactivityTimer) {
        clearTimeout(this.inactivityTimer)
        this.inactivityTimer = null
      }
    },

    // 🚪 DÉCONNEXION AUTOMATIQUE (appelée par le timer)
    async autoLogout() {
      console.log('🚪 Déconnexion automatique en cours...')
      await this.signOut()
      // Le router va rediriger automatiquement vers /login grâce au watcher dans App.vue
    },

    // 🔐 CONNEXION avec email + mot de passe
    async signIn(email, password) {
      this.loading = true
      this.error = null
      
      try {
        // Appel à Supabase pour se connecter
        const { data, error } = await supabase.auth.signInWithPassword({
          email: email,
          password: password
        })
        
        if (error) {
          // Si erreur, on la stocke pour l'afficher
          this.error = error.message
          console.error('Erreur de connexion:', error)
          return { success: false, error: error.message }
        }
        
        // ✅ Connexion réussie !
        this.user = data.user
        console.log('✅ Connexion réussie:', this.user.email)
        
        // ⏰ Démarrer le timer d'inactivité après la connexion
        this.startInactivityTimer()
        
        return { success: true }
        
      } catch (err) {
        this.error = err.message
        console.error('Erreur inattendue:', err)
        return { success: false, error: err.message }
      } finally {
        this.loading = false
      }
    },

    // 🚪 DÉCONNEXION
    async signOut() {
      this.loading = true
      this.error = null
      
      // ⏰ Arrêter le timer d'inactivité
      this.clearInactivityTimer()
      
      try {
        const { error } = await supabase.auth.signOut()
        
        if (error) {
          this.error = error.message
          console.error('Erreur de déconnexion:', error)
          return { success: false }
        }
        
        // ✅ Déconnexion réussie
        this.user = null
        console.log('👋 Déconnexion réussie')
        return { success: true }
        
      } catch (err) {
        this.error = err.message
        console.error('Erreur inattendue:', err)
        return { success: false }
      } finally {
        this.loading = false
      }
    },

    // 🔄 CHANGER LE MOT DE PASSE
    async changePassword(newPassword) {
      this.loading = true
      this.error = null
      
      try {
        const { data, error } = await supabase.auth.updateUser({
          password: newPassword
        })
        
        if (error) {
          this.error = error.message
          console.error('Erreur changement mot de passe:', error)
          return { success: false, error: error.message }
        }
        
        // ✅ Mot de passe changé
        console.log('✅ Mot de passe changé avec succès')
        return { success: true }
        
      } catch (err) {
        this.error = err.message
        console.error('Erreur inattendue:', err)
        return { success: false, error: err.message }
      } finally {
        this.loading = false
      }
    },

    // 🔍 VÉRIFIER si un utilisateur est déjà connecté (au chargement de l'app)
    async checkUser() {
      this.loading = true
      
      try {
        // Demande à Supabase : "Y a-t-il quelqu'un de connecté ?"
        const { data: { user } } = await supabase.auth.getUser()
        
        if (user) {
          this.user = user
          console.log('👤 Utilisateur trouvé:', user.email)
          
          // ⏰ Démarrer le timer d'inactivité si l'utilisateur est connecté
          this.startInactivityTimer()
        } else {
          this.user = null
          console.log('❌ Aucun utilisateur connecté')
        }
        
        return user
        
      } catch (err) {
        console.error('Erreur vérification utilisateur:', err)
        this.user = null
        return null
      } finally {
        this.loading = false
      }
    },

    // 👂 ÉCOUTER les changements d'état d'authentification
    // (par exemple, si l'utilisateur se connecte dans un autre onglet)
    initAuthListener() {
      supabase.auth.onAuthStateChange((event, session) => {
        console.log('🔔 Changement d\'auth:', event)
        
        if (session?.user) {
          this.user = session.user
          // ⏰ Redémarrer le timer si l'utilisateur se connecte
          this.startInactivityTimer()
        } else {
          this.user = null
          // ⏰ Arrêter le timer si l'utilisateur se déconnecte
          this.clearInactivityTimer()
        }
      })
    }
  }
})