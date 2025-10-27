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
    error: null
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
        } else {
          this.user = null
        }
      })
    }
  }
})
