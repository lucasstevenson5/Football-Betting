import { useState, useEffect } from 'react';
import './PukaNacuaGuide.css';

/**
 * PukaNacuaGuide - Interactive guide with Puka Nacua for Parlay Builder
 * Walks users through building their first parlay step by step
 */
const PukaNacuaGuide = ({
  createParlayClicked,
  playerAddedToParlay,
  statlineAddedToParlay,
  sportsbookOddsEntered,
  parlaySaved
}) => {
  const [guideStep, setGuideStep] = useState(0);
  const [isMinimized, setIsMinimized] = useState(false);
  const [hasSeenGuide, setHasSeenGuide] = useState(false);

  // Check if user has seen the guide before
  useEffect(() => {
    const seen = localStorage.getItem('pukaGuideSeen');
    if (seen) {
      setHasSeenGuide(true);
      setIsMinimized(true);
    }
  }, []);

  // React to "Create New Parlay" being clicked
  useEffect(() => {
    if (createParlayClicked && guideStep === 0) {
      setGuideStep(1); // Move from intro to "add a player"
    }
  }, [createParlayClicked, guideStep]);

  // React to player being added to parlay
  useEffect(() => {
    if (playerAddedToParlay && guideStep === 1) {
      setGuideStep(2); // Move from "add a player" to "choose statline"
    }
  }, [playerAddedToParlay, guideStep]);

  // React to statline being added to parlay
  useEffect(() => {
    if (statlineAddedToParlay && guideStep === 2) {
      setGuideStep(3); // Move from "choose statline" to "enter odds"
    }
  }, [statlineAddedToParlay, guideStep]);

  // React to sportsbook odds being entered
  useEffect(() => {
    if (sportsbookOddsEntered && guideStep === 3) {
      setGuideStep(4); // Move from "enter odds" to "save parlay"
    }
  }, [sportsbookOddsEntered, guideStep]);

  // React to parlay being saved
  useEffect(() => {
    if (parlaySaved && guideStep === 4) {
      setGuideStep(5); // Move to final message
    }
  }, [parlaySaved, guideStep]);

  // Messages for each step
  const getGuideMessage = () => {
    switch (guideStep) {
      case 0:
        return "So you want to build your first parlay?";
      case 1:
        return "Great! Lets start off by adding a player. May I suggest the Mr. Reliable? *cough* Puka Nacua *cough*";
      case 2:
        return "Now choose your statline and lets get it added to our parlay!";
      case 3:
        return "Now scroll down and tell me how much you want to bet and what Vegas thinks the odds are and see if we're getting a good deal.";
      case 4:
        return "Great, continue adding players or scroll up and press Save Parlay to save it off";
      case 5:
        return "Great looking parlay! Go Rams! 🏈";
      default:
        return "Welcome to Parlay Builder!";
    }
  };

  const handlePukaClick = () => {
    // Advance to next step when clicking on Puka
    if (guideStep < 5) {
      setGuideStep(guideStep + 1);
    }
  };

  const handleClose = () => {
    setIsMinimized(true);
    localStorage.setItem('pukaGuideSeen', 'true');
    setHasSeenGuide(true);
  };

  const handleReopen = () => {
    setIsMinimized(false);
  };

  const handleReset = () => {
    setGuideStep(0);
    setHasSeenGuide(false);
    setIsMinimized(false);
    localStorage.removeItem('pukaGuideSeen');
  };

  if (isMinimized) {
    return (
      <div className="puka-guide minimized" onClick={handleReopen}>
        <img
          src="/assets/players/PukaNacuaCartoon.PNG"
          alt="Puka Nacua"
          className="puka-minimized-image"
        />
        <div className="puka-minimized-tooltip">Click for help!</div>
      </div>
    );
  }

  return (
    <div className="puka-guide">
      <button className="puka-close" onClick={handleClose}>×</button>

      <div className="puka-container">
        <img
          src="/assets/players/PukaNacuaCartoon.PNG"
          alt="Puka Nacua"
          className="puka-image"
          onClick={handlePukaClick}
        />

        <div className="puka-speech-bubble">
          <div className="puka-message">{getGuideMessage()}</div>

          {guideStep === 5 && (
            <button className="puka-reset" onClick={handleReset}>
              Start Over
            </button>
          )}
        </div>
      </div>
    </div>
  );
};

export default PukaNacuaGuide;
