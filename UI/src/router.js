import { createRouter, createWebHistory } from "vue-router";
import { useAuthStore } from "./stores/authStore";

import Login from "./views/Login.vue";
import Password from "./views/Password.vue";
import Console from "./views/HomePreview.vue";
import Editor from "./views/Editor.vue";
import Announcement from "./views/AnnouncementDisplay.vue";
import Settings from "./views/Settings.vue";
import ForgotPassword from "./views/ForgotPassword.vue";
import ResetPassword from "./views/ResetPassword.vue";
import MainDisplay from "./views/STMDisplay.vue";


// 🗺️ DÉFINITION DES ROUTES
const routes = [
  // ==========================================
  // ROUTES PUBLIQUES
  // ==========================================
  {
    path: "/login",
    name: "Login",
    component: Login,
    meta: { requiresAuth: false }, 
  },
  {
    path: "/password",
    name: "Password",
    component: Password,
    meta: { requiresAuth: false }, 
  },
  {
    path: "/display",
    name: "Display",
    component: Announcement,
    meta: { requiresAuth: false }, 
  },
  {
    path: "/forgot-password",
    name: "ForgotPassword",
    component: ForgotPassword,
    meta: { requiresAuth: false },
  },
  {
    path: "/reset-password",
    name: "ResetPassword",
    component: ResetPassword,
    meta: { requiresAuth: false },
  },
  // ==========================================
  // ROUTES PROTÉGÉES (besoin d'être connecté)
  // ==========================================
  {
    path: "/",
    name: "Home",
    component: Console, 
    meta: { requiresAuth: true }, 
  },
  {
    path: "/editor",
    name: "Editor",
    component: Editor,
    meta: { requiresAuth: true }, 
  },
  {
    path: "/settings",
    name: "Settings",
    component: Settings,
    meta: { requiresAuth: true }, 
  },
  {
    path: "/stm",
    name: "STM",
    component: MainDisplay,
    meta: {requiresAuth : true},
  },

  // ==========================================
  // ROUTE 404 (page non trouvée)
  // ==========================================
  {
    path: "/:pathMatch(.*)*",
    redirect: "/login", 
  },
];

// CRÉATION DU ROUTER
const router = createRouter({
  history: createWebHistory(),
  routes,
});

// PROTECTION DES ROUTES
router.beforeEach(async (to, from, next) => {
  console.log("🔄 Navigation vers:", to.path);

  // Récupérer le store d'authentification
  const authStore = useAuthStore();

  // Vérifier si l'utilisateur est connecté
  const user = await authStore.checkUser();

  const requiresAuth = to.matched.some((record) => record.meta.requiresAuth);

  if (requiresAuth && !user) {
    console.log("🚫 Accès refusé - Redirection vers /login");
    next("/login");
  } else if (!requiresAuth && user && to.path === "/login") {
    console.log("✅ Déjà connecté - Redirection vers /");
    next("/");
  } else {
    console.log("✅ Navigation autorisée");
    next();
  }
});

export default router;
