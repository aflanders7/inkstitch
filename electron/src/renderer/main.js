/*
 * Authors: see git history
 *
 * Copyright (c) 2010 Authors
 * Licensed under the GNU GPL version 3.0 or later.  See the file LICENSE for details.
 *
 */

// ES6
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import { library } from '@fortawesome/fontawesome-svg-core'
import { fas } from '@fortawesome/free-solid-svg-icons'
import { FontAwesomeIcon, FontAwesomeLayers } from '@fortawesome/vue-fontawesome'
import { createGettext } from 'vue3-gettext'
import translations from './assets/translations.json'
import { selectLanguage } from '../lib/i18n.js'

library.add(fas)
const app = createApp(App)
app.component('font-awesome-icon', FontAwesomeIcon)
app.component('font-awesome-layers', FontAwesomeLayers)

app.use(createGettext({
    defaultLanguage: selectLanguage(translations),
    translations: translations,
    silent: true,
    setGlobalProperties: true,
})
)
app.use(router)
app.mount('#app')
