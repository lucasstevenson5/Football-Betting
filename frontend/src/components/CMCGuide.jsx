import { useState, useEffect } from 'react';
import './CMCGuide.css';

/**
 * CMCGuide - Interactive guide with Christian McCaffrey
 * Walks users through the app features step by step
 */
const CMCGuide = ({ activeTab, onPlayerClick }) => {
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

  // Guide progression based on tab changes
  useEffect(() => {
    if (hasSeenGuide) return;

    // Auto-advance based on tab navigation
    if (activeTab === 'players' && guideStep === 0) {
      // Stay on step 0 - initial message
    } else if (activeTab === 'players' && guideStep > 0) {
      // User came back to players tab
    } else if (activeTab === 'accuracy' && guideStep < 2) {
      // User went to accuracy tab
      setGuideStep(2);
    } else if (activeTab === 'accuracy' && guideStep === 2) {
      // Show final message after brief delay
      setTimeout(() => {
        setGuideStep(3);
      }, 1500);
    }
  }, [activeTab, guideStep, hasSeenGuide]);

  // Messages for each step
  const getGuideMessage = () => {
    switch (guideStep) {
      case 0:
        return "Click on a player, may I suggest Christian McCaffrey? Then check out the Predictions tab!";
      case 1:
        return "Great! Now check out the Model Accuracy tab to see how we're doing!";
      case 2:
        return "Awesome! Check out our accuracy tracking.";
      case 3:
        return "Have fun and go 49ers! 🏈";
      default:
        return "Welcome! Let me show you around.";
    }
  };

  const handleCMCClick = () => {
    // Advance to next step when clicking on CMC
    if (guideStep < 3) {
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

          {guideStep === 3 && (
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
