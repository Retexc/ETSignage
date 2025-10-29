
import { createClient } from '@supabase/supabase-js'

const supabaseUrl = 'https://xaxwozhoyxyalqhbhlid.supabase.co' 
const supabaseAnonKey = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6InhheHdvemhveXh5YWxxaGJobGlkIiwicm9sZSI6ImFub24iLCJpYXQiOjE3NjE0MDcyNzksImV4cCI6MjA3Njk4MzI3OX0.SQJRxNo3aEsGIYjBT5_FUADADs2rw4m11ok0-g1Q8aA'  // La longue clé "anon public"

// Création du client Supabase
export const supabase = createClient(supabaseUrl, supabaseAnonKey)


