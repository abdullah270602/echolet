// The example call in the demo panel and the ticket further down the page tell one
// story; "See the ticket it wrote" scrolls to the ticket and replays its write-in.
const EVENT = 'echolet:show-ticket';

export function showTicket() {
  document.getElementById('message')?.scrollIntoView({ behavior: 'smooth' });
  window.dispatchEvent(new Event(EVENT));
}

export function onShowTicket(listener: () => void) {
  window.addEventListener(EVENT, listener);
  return () => window.removeEventListener(EVENT, listener);
}
