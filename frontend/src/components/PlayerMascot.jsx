import { useState, useEffect } from 'react';
import { getAllPlayerImages } from '../utils/playerImages';
import './PlayerMascot.css';

/**
 * PlayerMascot - Displays rotating player cartoon images
 * Can be used as a fun visual element on the homepage
 */
const PlayerMascot = ({
  autoRotate = true,
  rotateInterval = 5000,
  size = 'medium' // 'small', 'medium', 'large'
}) => {
  const players = getAllPlayerImages();
  const [currentPlayerIndex, setCurrentPlayerIndex] = useState(0);

  useEffect(() => {
    if (!autoRotate) return;

    const interval = setInterval(() => {
      setCurrentPlayerIndex((prevIndex) => (prevIndex + 1) % players.length);
    }, rotateInterval);

    return () => clearInterval(interval);
  }, [autoRotate, rotateInterval, players.length]);

  const currentPlayer = players[currentPlayerIndex];

  const handlePrevious = () => {
    setCurrentPlayerIndex((prevIndex) =>
      prevIndex === 0 ? players.length - 1 : prevIndex - 1
    );
  };

  const handleNext = () => {
    setCurrentPlayerIndex((prevIndex) => (prevIndex + 1) % players.length);
  };

  return (
    <div className={`player-mascot player-mascot-${size}`}>
      <div className="mascot-container">
        <button className="mascot-nav-button prev" onClick={handlePrevious}>
          ‹
        </button>

        <div className="mascot-content">
          <img
            src={currentPlayer.image}
            alt={currentPlayer.name}
            className="mascot-image"
          />
          <div className="mascot-name">{currentPlayer.name}</div>
          <div className="mascot-indicator">
            {players.map((_, index) => (
              <span
                key={index}
                className={`indicator-dot ${index === currentPlayerIndex ? 'active' : ''}`}
                onClick={() => setCurrentPlayerIndex(index)}
              />
            ))}
          </div>
        </div>

        <button className="mascot-nav-button next" onClick={handleNext}>
          ›
        </button>
      </div>
    </div>
  );
};

export default PlayerMascot;
