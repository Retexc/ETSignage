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
    isPaused: false
  }),

  getters: {
    // Obtenir les annonces avec média seulement
    annoncesAvecMedia: (state) => {
      return state.annonces.filter(a => a.media !== null)
    },
    
    // Obtenir l'annonce actuellement affichée
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
    // Ajouter une nouvelle annonce
    ajouterAnnonce(annonce) {
      this.annonces.push(annonce)
    },
    
    // Mettre à jour une annonce existante
    mettreAJourAnnonce(id, data) {
      const index = this.annonces.findIndex(a => a.id === id)
      if (index !== -1) {
        this.annonces[index] = { ...this.annonces[index], ...data }
      }
    },
    
    // Supprimer une annonce
    supprimerAnnonce(id) {
      const index = this.annonces.findIndex(a => a.id === id)
      if (index !== -1) {
        this.annonces.splice(index, 1)
      }
    },
    
    // Remplacer toutes les annonces (depuis l'éditeur)
    setAnnonces(annonces) {
      this.annonces = annonces
    },
    
    // Passer à la page suivante
    pageSuivante() {
      const annoncesValides = this.annonces.filter(a => a.media !== null)
      if (annoncesValides.length > 0) {
        this.pageActuelle = (this.pageActuelle + 1) % annoncesValides.length
      }
    },
    
    // Aller à une page spécifique
    allerALaPage(index) {
      const annoncesValides = this.annonces.filter(a => a.media !== null)
      if (index >= 0 && index < annoncesValides.length) {
        this.pageActuelle = index
      }
    },
    
    // Démarrer la lecture
    demarrerLecture() {
      this.isPlaying = true
      this.isPaused = false
    },
    
    // Mettre en pause
    pauseLecture() {
      this.isPaused = true
    },
    
    // Reprendre la lecture
    reprendreLecture() {
      this.isPaused = false
    },
    
    // Arrêter la lecture
    arreterLecture() {
      this.isPlaying = false
      this.isPaused = false
      this.pageActuelle = 0
    },
    
    // Sauvegarder dans localStorage
    sauvegarderLocal() {
      localStorage.setItem('annonces', JSON.stringify(this.annonces))
    },
    
    // Charger depuis localStorage
    chargerLocal() {
      const saved = localStorage.getItem('annonces')
      if (saved) {
        try {
          this.annonces = JSON.parse(saved)
        } catch (e) {
          console.error('Erreur lors du chargement des annonces:', e)
        }
      }
    }
  }
})