import { createApp } from "vue";
import { Quasar, Notify } from "quasar";
import quasarLang from "quasar/lang/ja";

import "@quasar/extras/material-icons/material-icons.css";

import "quasar/src/css/index.sass";

import App from "./App.vue";

const myApp = createApp(App);

myApp.use(Quasar, {
  plugins: {
    Notify
  },
  lang: quasarLang,
});

myApp.mount("#app");