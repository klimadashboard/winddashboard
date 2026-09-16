// SSR an, damit Titel, Beschreibung und Social-Karte im ausgelieferten HTML
// stehen und der Einstiegstext für Suchmaschinen sichtbar ist. Karte, Story und
// Partikel sind im Layout hinter `browser` abgeschirmt und laufen weiterhin nur
// im Client.
export const ssr = true;
export const prerender = false;
