/**
 * Player Cartoon Images
 * Maps player names to their cartoon image files
 */

export const PLAYER_IMAGES = {
  'Brock Bowers': '/assets/players/BrockBowerCartoon.PNG',
  'Christian McCaffrey': '/assets/players/ChristianMcCaffreyCartoon.PNG',
  "Ja'Marr Chase": '/assets/players/JamarrChaseCartoon.PNG',
  'Josh Allen': '/assets/players/JoshAllenCartoon.PNG',
  'Justin Jefferson': '/assets/players/JustinJeffersonCartoon.PNG',
  'Puka Nacua': '/assets/players/PukaNacuaCartoon.PNG',
  'Saquon Barkley': '/assets/players/SaquonBarkleyCartoon.PNG',
  'Tom Brady': '/assets/players/TomBradyCartoon.PNG',
  'Trey McBride': '/assets/players/TreyMcbrideCartoon.PNG'
};

/**
 * Get player image by name
 * @param {string} playerName - Full player name
 * @returns {string|null} - Image path or null if not found
 */
export const getPlayerImage = (playerName) => {
  return PLAYER_IMAGES[playerName] || null;
};

/**
 * Get all available player images
 * @returns {Array} - Array of {name, image} objects
 */
export const getAllPlayerImages = () => {
  return Object.entries(PLAYER_IMAGES).map(([name, image]) => ({
    name,
    image
  }));
};

/**
 * Get a random player image
 * @returns {Object} - {name, image}
 */
export const getRandomPlayerImage = () => {
  const players = getAllPlayerImages();
  return players[Math.floor(Math.random() * players.length)];
};
