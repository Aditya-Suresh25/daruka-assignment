import js from '@eslint/js'
import reactHooks from 'eslint-plugin-react-hooks'
import parser from '@typescript-eslint/parser'
export default [js.configs.recommended,{files:['**/*.{ts,tsx}'],languageOptions:{parser,globals:{window:'readonly',document:'readonly',fetch:'readonly',localStorage:'readonly',URLSearchParams:'readonly'}},plugins:{'react-hooks':reactHooks},rules:{'no-undef':'off','no-unused-vars':'off','react-hooks/rules-of-hooks':'error','react-hooks/exhaustive-deps':'warn'}},{ignores:['dist']}]