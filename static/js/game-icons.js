/**
 * Fallback icon URLs for non-Steam games
 * Uses publicly available CDN sources
 */
const FALLBACK_GAME_ICONS = {
    "Fortnite": "https://cdn2.unrealengine.com/fortnite-logo-1920x1080-15db0d9f5d0e.jpg",
    "VALORANT": "https://images.contentstack.io/v3/assets/bltb6530b271fddd0b1/blt3b1a2b49f9e0a53b/62c8dcbc21c27e1cc4055b8f/valorant_logo_red.png",
    "Roblox": "https://images.rbxcdn.com/c69b74f49c785738a8d8b23d3dea87e7.jpg",
    "League of Legends": "https://lolstatic-a.akamaihd.net/rso-login/images/lol-logo.png",
    "Apex Legends": null, // On Steam, will use Steam CDN
    "Overwatch": "https://images.blz-contentstack.com/v3/assets/blt2477dcaf4ebd440c/blt6af70e671d6a14bb/62ea39db89efb30900dba69b/ow-logomark-orange.png",
    "Overwatch 2": "https://images.blz-contentstack.com/v3/assets/blt2477dcaf4ebd440c/blt6af70e671d6a14bb/62ea39db89efb30900dba69b/ow-logomark-orange.png",
};

/**
 * Generic game icon placeholder as data URL
 * Simple gradient with game controller emoji
 */
const GENERIC_GAME_ICON = 'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iMTg0IiBoZWlnaHQ9IjY5IiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPjxkZWZzPjxsaW5lYXJHcmFkaWVudCBpZD0iZyIgeDE9IjAlIiB5MT0iMCUiIHgyPSIxMDAlIiB5Mj0iMTAwJSI+PHN0b3Agb2Zmc2V0PSIwJSIgc3R5bGU9InN0b3AtY29sb3I6IzNiODJmNjtzdG9wLW9wYWNpdHk6MC4zIi8+PHN0b3Agb2Zmc2V0PSIxMDAlIiBzdHlsZT0ic3RvcC1jb2xvcjojMWRiOTU0O3N0b3Atb3BhY2l0eTowLjMiLz48L2xpbmVhckdyYWRpZW50PjwvZGVmcz48cmVjdCB3aWR0aD0iMTg0IiBoZWlnaHQ9IjY5IiBmaWxsPSJ1cmwoI2cpIiByeD0iNCIvPjx0ZXh0IHg9IjUwJSIgeT0iNTAlIiBmb250LXNpemU9IjI0IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBkb21pbmFudC1iYXNlbGluZT0ibWlkZGxlIj7wn46uPC90ZXh0Pjwvc3ZnPg==';

/**
 * Handle game icon loading errors with fallback
 * @param {HTMLImageElement} img - The image element that failed to load
 * @param {string} gameName - Name of the game
 */
function handleGameIconError(img, gameName) {
    // Try fallback URL first
    if (FALLBACK_GAME_ICONS[gameName] && img.src !== FALLBACK_GAME_ICONS[gameName]) {
        img.src = FALLBACK_GAME_ICONS[gameName];
        img.style.width = 'auto';
        img.style.maxWidth = '46px';
        img.style.maxHeight = '22px';
        return;
    }
    
    // Use generic placeholder
    img.src = GENERIC_GAME_ICON;
    img.style.opacity = '0.6';
}

// Export for use in inline handlers
window.handleGameIconError = handleGameIconError;
