// stores/annonceStore.js
import { defineStore } from 'pinia'

export const useAnnonceStore = defineStore('annonce', {
  state: () => ({
    // Liste des annonces/pages créées dans l'éditeur
    annonces: [
      {
        id: 1,
        nom: "Page 1",
        media: null,
        mediaType: null,
        mediaName: null,
        mediaSize: null,
        dureeDebut: "",
        dureeFin: "",
        dureeAffichage: 5,
        transition: "fade",
        modeAffichage: "cover",
        loop: false,
      }
    ],
    // Index de la page actuellement affichée
    pageActuelle: 0,
    // État de lecture
    isPlaying: false,
    isPaused: false,
    // 🆕 NOUVEAU : Version pour forcer le rechargement des composants
    version: 0
  }),

  getters: {

    annoncesAvecMedia: (state) => {
      return state.annonces.filter(a => a.media !== null)
    },
    

    annonceActuelle: (state) => {
      const annoncesValides = state.annonces.filter(a => a.media !== null)
      if (annoncesValides.length === 0) return null
      return annoncesValides[state.pageActuelle % annoncesValides.length]
    },
    
    // Nombre total d'annonces avec média
    totalAnnonces: (state) => {
      return state.annonces.filter(a => a.media !== null).length
    }
  },

  actions: {

    ajouterAnnonce(annonce) {
      this.annonces.push(annonce)
      // 🆕 Notifier le changement
      this.notifierChangement()
    },
    
  
    mettreAJourAnnonce(id, data) {
      const index = this.annonces.findIndex(a => a.id === id)
      if (index !== -1) {
        this.annonces[index] = { ...this.annonces[index], ...data }
        // 🆕 Notifier le changement
        this.notifierChangement()
      }
    },
    
    // Supprimer une annonce
    supprimerAnnonce(id) {
      const index = this.annonces.findIndex(a => a.id === id)
      if (index !== -1) {
        this.annonces.splice(index, 1)
        // 🆕 Notifier le changement
        this.notifierChangement()
      }
    },
    
   
    setAnnonces(annonces) {
      this.annonces = annonces
      // 🆕 Notifier le changement
      this.notifierChangement()
    },
    

    pageSuivante() {
      const annoncesValides = this.annonces.filter(a => a.media !== null)
      if (annoncesValides.length > 0) {
        this.pageActuelle = (this.pageActuelle + 1) % annoncesValides.length
        // 🆕 Sauvegarder et notifier
        this.sauvegarderEtat()
        this.notifierChangement()
      }
    },
    

    allerALaPage(index) {
      const annoncesValides = this.annonces.filter(a => a.media !== null)
      if (index >= 0 && index < annoncesValides.length) {
        this.pageActuelle = index
        // 🆕 Sauvegarder et notifier
        this.sauvegarderEtat()
        this.notifierChangement()
      }
    },
    

    demarrerLecture() {
      this.isPlaying = true
      this.isPaused = false
      this.sauvegarderEtat()
      this.notifierChangement()
    },
    

    pauseLecture() {
      this.isPaused = true
      this.sauvegarderEtat()
      this.notifierChangement()
    },
    

    reprendreLecture() {
      this.isPaused = false
      this.sauvegarderEtat()
      this.notifierChangement()
    },
    

    arreterLecture() {
      this.isPlaying = false
      this.isPaused = false
      this.pageActuelle = 0
      this.sauvegarderEtat()
      this.notifierChangement()
    },
    

    sauvegarderLocal() {
      localStorage.setItem('annonces', JSON.stringify(this.annonces))
      // 🆕 Notifier le changement
      this.notifierChangement()
    },
    
    // 🆕 NOUVELLE FONCTION : Sauvegarder l'état de la lecture
    sauvegarderEtat() {
      const etat = {
        pageActuelle: this.pageActuelle,
        isPlaying: this.isPlaying,
        isPaused: this.isPaused,
        version: this.version,
        timestamp: Date.now()
      }
      localStorage.setItem('annonceState', JSON.stringify(etat))
      console.log('💾 État sauvegardé:', etat)
    },

    // 🆕 NOUVELLE FONCTION : Charger l'état de la lecture
    chargerEtat() {
      const saved = localStorage.getItem('annonceState')
      if (saved) {
        try {
          const etat = JSON.parse(saved)
          this.pageActuelle = etat.pageActuelle || 0
          this.isPlaying = etat.isPlaying || false
          this.isPaused = etat.isPaused || false
          this.version = etat.version || 0
          console.log('📂 État chargé:', etat)
        } catch (e) {
          console.error('Erreur lors du chargement de l\'état:', e)
        }
      }
    },
 
    chargerLocal() {
      const saved = localStorage.getItem('annonces')
      if (saved) {
        try {
          this.annonces = JSON.parse(saved)
        } catch (e) {
          console.error('Erreur lors du chargement des annonces:', e)
        }
      }
      this.chargerEtat()
    },

    // 🆕 NOUVELLE FONCTION : Notifier tous les composants d'un changement
    notifierChangement() {
      // Incrémenter la version
      this.version++
      
      // Sauvegarder l'état avec la nouvelle version
      this.sauvegarderEtat()
      
      // Émettre un événement personnalisé pour notifier tous les composants
      window.dispatchEvent(new CustomEvent('annonce-changed', { 
        detail: { 
          version: this.version,
          pageActuelle: this.pageActuelle,
          timestamp: Date.now()
        } 
      }))
      
      console.log('📢 Changement notifié - Version:', this.version)
    }
  }
})