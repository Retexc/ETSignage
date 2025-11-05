import { defineStore } from 'pinia'
import { supabase } from '../lib/supabaseClient.js'

export const useAnnonceStore = defineStore('annonce', {
  state: () => ({
    annonces: [],
    pageActuelle: 0,
    isPlaying: false,
    isPaused: false
  }),

  getters: {
    annonceActive: (state) => state.annonces[state.pageActuelle] || null,
    hasAnnonces: (state) => state.annonces.length > 0,
    totalAnnonces: (state) => state.annonces.length
  },

  actions: {
    // 📤 Sauvegarder les annonces dans Supabase
    async sauvegarderAnnonces(annonces) {
      try {
        console.log('💾 Sauvegarde des annonces dans Supabase...')
        
        // Convertir en JSON
        const jsonData = JSON.stringify(annonces, null, 2)
        const blob = new Blob([jsonData], { type: 'application/json' })
        
        // Supprimer l'ancien fichier s'il existe
        const { error: removeError } = await supabase.storage
          .from('backgrounds')
          .remove(['annonces.json'])
        
        if (removeError) {
          console.log('⚠️ Pas de fichier précédent à supprimer')
        }
        
        // Upload le nouveau fichier
        const { data, error } = await supabase.storage
          .from('backgrounds')
          .upload('annonces.json', blob, {
            cacheControl: '0', // Pas de cache
            upsert: true
          })
        
        if (error) {
          console.error('❌ Erreur sauvegarde Supabase:', error)
          // Fallback sur localStorage en cas d'erreur
          localStorage.setItem('annonces', JSON.stringify(annonces))
          return false
        }
        
        console.log('✅ Annonces sauvegardées dans Supabase!', data)
        this.annonces = annonces
        
        // Sauvegarder aussi en local comme backup
        localStorage.setItem('annonces', JSON.stringify(annonces))
        return true
        
      } catch (err) {
        console.error('❌ Erreur inattendue:', err)
        // Fallback sur localStorage
        localStorage.setItem('annonces', JSON.stringify(annonces))
        return false
      }
    },

    // 📥 Charger les annonces depuis Supabase
    async chargerAnnonces() {
      try {
        console.log('📥 Chargement des annonces depuis Supabase...')
        
        // Ajouter un timestamp pour forcer le bypass du cache
        const timestamp = Date.now()
        
        // Télécharger le fichier depuis Supabase avec bypass du cache
        const { data, error } = await supabase.storage
          .from('backgrounds')
          .download(`annonces.json?t=${timestamp}`)
        
        if (error) {
          console.warn('⚠️ Fichier annonces.json non trouvé dans Supabase:', error.message)
          console.log('🔄 Tentative de chargement depuis localStorage...')
          // Fallback sur localStorage
          return this.chargerLocal()
        }
        
        if (!data) {
          console.warn('⚠️ Pas de données reçues de Supabase')
          return this.chargerLocal()
        }
        
        // Lire le contenu du fichier
        const text = await data.text()
        
        if (!text || text.trim() === '') {
          console.warn('⚠️ Fichier vide dans Supabase')
          return this.chargerLocal()
        }
        
        const annonces = JSON.parse(text)
        console.log('📄 Annonces brutes chargées:', annonces.length)
        
        // 🔧 IMPORTANT : Reconstruire les mediaURL pour chaque annonce
        annonces.forEach(annonce => {
          if (annonce.media) {
            // Reconstruire l'URL publique depuis le nom du fichier
            const { data: urlData } = supabase.storage
              .from('backgrounds')
              .getPublicUrl(annonce.media)
            
            annonce.mediaURL = urlData.publicUrl
            console.log('🔗 URL reconstruite:', annonce.nom, '→', urlData.publicUrl)
          }
        })
        
        this.annonces = annonces
        console.log('✅ Annonces chargées depuis Supabase:', annonces.length, 'pages')
        
        // Sauvegarder en local comme backup
        localStorage.setItem('annonces', JSON.stringify(annonces))
        return true
        
      } catch (err) {
        console.error('❌ Erreur chargement Supabase:', err)
        console.log('🔄 Fallback sur localStorage')
        // Fallback sur localStorage
        return this.chargerLocal()
      }
    },

    // 📂 Charger depuis localStorage (fallback)
    chargerLocal() {
      const saved = localStorage.getItem('annonces')
      if (saved) {
        try {
          const annonces = JSON.parse(saved)
          console.log('📄 Annonces depuis localStorage:', annonces.length)
          
          // 🔧 Reconstruire les mediaURL pour chaque annonce
          annonces.forEach(annonce => {
            if (annonce.media) {
              const { data: urlData } = supabase.storage
                .from('backgrounds')
                .getPublicUrl(annonce.media)
              
              annonce.mediaURL = urlData.publicUrl
              console.log('🔗 URL reconstruite (local):', annonce.nom)
            }
          })
          
          this.annonces = annonces
          console.log('✅ Annonces chargées depuis localStorage')
          return true
        } catch (e) {
          console.error('❌ Erreur chargement localStorage:', e)
          return false
        }
      }
      console.warn('⚠️ Aucune annonce dans localStorage')
      return false
    },

    // Navigation
    pageSuivante() {
      if (this.annonces.length > 0) {
        this.pageActuelle = (this.pageActuelle + 1) % this.annonces.length
      }
    },

    allerALaPage(index) {
      if (index >= 0 && index < this.annonces.length) {
        this.pageActuelle = index
      }
    },

    // Lecture
    demarrerLecture() {
      this.isPlaying = true
      this.isPaused = false
    },

    pauseLecture() {
      this.isPaused = true
    },

    reprendreLecture() {
      this.isPaused = false
    },

    arreterLecture() {
      this.isPlaying = false
      this.isPaused = false
      this.pageActuelle = 0
    }
  }
})