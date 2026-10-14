// Tiny shared store for short "Saved" / "Deleted" messages shown at the top of the page.
import { reactive } from 'vue';

export const flash = reactive({ text: '', kind: 'success' });

let timer;
export function showFlash(text, kind = 'success') {
  flash.text = text;
  flash.kind = kind;
  clearTimeout(timer);
  timer = setTimeout(() => (flash.text = ''), 3000);
}
