// src/lib/supabaseStorage.js
import { supabase } from './supabaseClient'

/**
 * 📤 Upload un fichier vers Supabase Storage
 * @param {File} file - Le fichier à uploader
 * @param {string} bucket - Le nom du bucket ('backgrounds' ou 'gtfs-files')
 * @param {string} folder - Sous-dossier optionnel (par exemple 'stm' ou 'exo')
 * @returns {Promise<{success: boolean, url: string|null, error: string|null}>}
 */
export async function uploadFile(file, bucket = 'backgrounds', folder = '') {
  try {
    // 1. Créer le chemin du fichier
    const timestamp = Date.now()
    const fileName = folder 
      ? `${folder}/${timestamp}-${file.name}` 
      : `${timestamp}-${file.name}`
    
    console.log(`📤 Upload vers ${bucket}/${fileName}...`)
    
    // 2. Upload le fichier
    const { data, error } = await supabase.storage
      .from(bucket)
      .upload(fileName, file, {
        cacheControl: '3600',
        upsert: false
      })
    
    if (error) {
      console.error('❌ Erreur upload:', error)
      return { success: false, url: null, error: error.message }
    }
    
    // 3. Récupérer l'URL publique
    const { data: urlData } = supabase.storage
      .from(bucket)
      .getPublicUrl(fileName)
    
    console.log('✅ Fichier uploadé:', urlData.publicUrl)
    return { success: true, url: urlData.publicUrl, error: null }
    
  } catch (err) {
    console.error('❌ Erreur inattendue:', err)
    return { success: false, url: null, error: err.message }
  }
}

/**
 * 🗑️ Supprimer un fichier de Supabase Storage
 * @param {string} fileUrl - L'URL complète du fichier
 * @param {string} bucket - Le nom du bucket
 */
export async function deleteFile(fileUrl, bucket = 'backgrounds') {
  try {
    // Extraire le nom du fichier depuis l'URL
    const urlParts = fileUrl.split('/')
    const fileName = urlParts[urlParts.length - 1]
    
    const { error } = await supabase.storage
      .from(bucket)
      .remove([fileName])
    
    if (error) {
      console.error('❌ Erreur suppression:', error)
      return { success: false, error: error.message }
    }
    
    console.log('✅ Fichier supprimé:', fileName)
    return { success: true, error: null }
    
  } catch (err) {
    console.error('❌ Erreur inattendue:', err)
    return { success: false, error: err.message }
  }
}

/**
 * 📋 Lister tous les fichiers d'un dossier
 * @param {string} bucket - Le nom du bucket
 * @param {string} folder - Le dossier à lister (ex: 'stm', 'exo')
 */
export async function listFiles(bucket = 'gtfs-files', folder = '') {
  try {
    const { data, error } = await supabase.storage
      .from(bucket)
      .list(folder, {
        limit: 100,
        offset: 0,
        sortBy: { column: 'created_at', order: 'desc' }
      })
    
    if (error) {
      console.error('❌ Erreur liste:', error)
      return { success: false, files: [], error: error.message }
    }
    
    return { success: true, files: data, error: null }
    
  } catch (err) {
    console.error('❌ Erreur inattendue:', err)
    return { success: false, files: [], error: err.message }
  }
}

/**
 * 📅 Récupérer la date du dernier fichier GTFS uploadé
 * @param {string} transport - 'stm' ou 'exo'
 */
export async function getLastGTFSUpdate(transport) {
  const result = await listFiles('gtfs-files', transport)
  
  if (!result.success || result.files.length === 0) {
    return 'N/A'
  }
  
  // Le premier fichier est le plus récent (trié par date)
  const lastFile = result.files[0]
  const date = new Date(lastFile.created_at)
  
  return date.toLocaleString('fr-CA', {
    year: 'numeric',
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}