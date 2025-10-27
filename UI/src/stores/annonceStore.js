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
    },
    
  
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
    
   
    setAnnonces(annonces) {
      this.annonces = annonces
    },
    

    pageSuivante() {
      const annoncesValides = this.annonces.filter(a => a.media !== null)
      if (annoncesValides.length > 0) {
        this.pageActuelle = (this.pageActuelle + 1) % annoncesValides.length
      }
    },
    

    allerALaPage(index) {
      const annoncesValides = this.annonces.filter(a => a.media !== null)
      if (index >= 0 && index < annoncesValides.length) {
        this.pageActuelle = index
      }
    },
    

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
    },
    

    sauvegarderLocal() {
      localStorage.setItem('annonces', JSON.stringify(this.annonces))
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
    }
  }
})