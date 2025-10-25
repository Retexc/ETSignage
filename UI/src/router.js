// src/router.js
import { createRouter, createWebHistory } from "vue-router";
import Background from "./views/Background.vue";
import Settings from "./views/Settings.vue";
import Console from "./views/Console.vue";
import Board from "./views/Board.vue";
import Display from "./views/MainDisplay.vue";
import Loading from "./views/Loading.vue";
import EndDisplay from "./views/EndDisplay.vue";
import TitleCard from "./views/TitleCard.vue";
import Editor from "./views/Editor.vue";
const routes = [
  { path: "/console", component: Console },
  { path: "/board", component: Board },
  { path: "/background", component: Background },
  { path: "/settings", component: Settings },
  { path: "/display", component: Display },
  { path: "/loading", component: Loading },
  { path: "/end_display", component: EndDisplay },
  { path: "/title_card", component: TitleCard },
  { path: "/editor", component: Editor },  
  { path: "/", redirect: "/console" },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
