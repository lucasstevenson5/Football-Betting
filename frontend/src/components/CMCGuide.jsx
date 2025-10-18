import { useState, useEffect } from 'react';
import './CMCGuide.css';

/**
 * CMCGuide - Interactive guide with Christian McCaffrey
 * Walks users through the app features step by step
 */
const CMCGuide = ({ activeTab, playerClicked }) => {
  const [guideStep, setGuideStep] = useState(0);
  const [isMinimized, setIsMinimized] = useState(false);
  const [hasSeenGuide, setHasSeenGuide] = useState(false);

  // Check if user has seen the guide before
  useEffect(() => {
    const seen = localStorage.getItem('cmcGuideSeen');
    if (seen) {
      setHasSeenGuide(true);
      setIsMinimized(true);
    }
  }, []);

  // React to player being clicked
  useEffect(() => {
    if (playerClicked && guideStep === 0) {
      setGuideStep(1); // Move from "click a player" to "check predictions tab"
    }
  }, [playerClicked, guideStep]);

  // Guide progression based on tab changes
  useEffect(() => {
    if (hasSeenGuide) return;

    // Auto-advance based on tab navigation
    if (activeTab === 'players' && guideStep === 0) {
      // Stay on step 0 - initial message
    } else if (activeTab === 'players' && guideStep === 1) {
      // User clicked a player and is viewing predictions, stay on step 1
    } else if (activeTab === 'accuracy' && guideStep === 2) {
      // User is on accuracy tab, move to step 3
      setGuideStep(3);
    } else if (activeTab === 'accuracy' && guideStep === 3) {
      // User is on accuracy tab at step 3, show final message after delay
      setTimeout(() => {
        setGuideStep(4);
      }, 1500);
    }
  }, [activeTab, guideStep, hasSeenGuide]);

  // Messages for each step
  const getGuideMessage = () => {
    switch (guideStep) {
      case 0:
        return "Click on a player, may I suggest Christian McCaffrey?";
      case 1:
        return "Check out the Predictions tab!";
      case 2:
        return "Great! Now check out the Model Accuracy tab to see how we're doing!";
      case 3:
        return "Awesome! Check out our accuracy tracking.";
      case 4:
        return "Have fun and go 49ers! 🏈";
      default:
        return "Welcome! Let me show you around.";
    }
  };

  const handleCMCClick = () => {
    // Advance to next step when clicking on CMC (simulates clicking a player)
    if (guideStep === 0) {
      setGuideStep(1); // Move from "click a player" to "check predictions tab"
    } else if (guideStep < 4) {
      setGuideStep(guideStep + 1);
    }
  };

  const handleClose = () => {
    setIsMinimized(true);
    localStorage.setItem('cmcGuideSeen', 'true');
    setHasSeenGuide(true);
  };

  const handleReopen = () => {
    setIsMinimized(false);
  };

  const handleReset = () => {
    setGuideStep(0);
    setHasSeenGuide(false);
    setIsMinimized(false);
    localStorage.removeItem('cmcGuideSeen');
  };

  if (isMinimized) {
    return (
      <div className="cmc-guide minimized" onClick={handleReopen}>
        <img
          src="/assets/players/ChristianMcCaffreyCartoon.PNG"
          alt="Christian McCaffrey"
          className="cmc-minimized-image"
        />
        <div className="cmc-minimized-tooltip">Click for help!</div>
      </div>
    );
  }

  return (
    <div className="cmc-guide">
      <button className="cmc-close" onClick={handleClose}>×</button>

      <div className="cmc-container">
        <img
          src="/assets/players/ChristianMcCaffreyCartoon.PNG"
          alt="Christian McCaffrey"
          className="cmc-image"
          onClick={handleCMCClick}
        />

        <div className="cmc-speech-bubble">
          <div className="cmc-message">{getGuideMessage()}</div>

          {guideStep === 4 && (
            <button className="cmc-reset" onClick={handleReset}>
              Start Over
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default CMCGuide;
