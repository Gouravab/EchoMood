import { useState, useEffect } from "react";
import { motion } from "framer-motion";
import "./MoodTracker.css";

export default function MoodTracker() {
  const [selectedMood, setSelectedMood] = useState(null);
  const [customMood, setCustomMood] = useState("");
  const [aiSuggestion, setAiSuggestion] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const moods = [
    { emoji: "😀", label: "Happy" },
    { emoji: "😢", label: "Sad" },
    { emoji: "😡", label: "Angry" },
    { emoji: "😱", label: "Anxious" },
    { emoji: "😌", label: "Calm" },
  ];

  useEffect(() => {
    console.log("Selected Mood:", selectedMood);
    console.log("Custom Mood:", customMood);
  }, [selectedMood, customMood]);

  const fetchAISuggestion = async (mood) => {
    if (!mood.trim()) {
      setAiSuggestion("Please select or enter a mood.");
      return;
    }

    setLoading(true);
    setAiSuggestion("");
    setError("");
    
    console.log("🔵 Sending API Request:", { mood });

    try {
      const response = await fetch(
        "https://3k8wbsyiyl.execute-api.us-east-1.amazonaws.com/dev/mood",
        {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            Accept: "application/json",
          },
          body: JSON.stringify({ mood }),
        }
      );

      console.log("🟢 API Response Status:", response.status);

      if (!response.ok) {
        throw new Error(`API request failed with status ${response.status}`);
      }

      const text = await response.text(); // Read response as text
      console.log("🟡 Raw API Response:", text);

      try {
        const data = JSON.parse(text);
        console.log("🟢 Parsed API Response:", data);
        setAiSuggestion(data.suggestion || "No suggestion available.");
      } catch (error) {
        console.error("🔴 Error parsing API response:", error);
        setAiSuggestion("Unexpected API response format.");
      }
    } catch (error) {
      console.error("🔴 API Error:", error);
      setError("Could not fetch AI suggestion. Try again later.");
    } finally {
      setLoading(false);
    }
  };

  const handleMoodSelection = (mood) => {
    setSelectedMood(mood);
    setCustomMood("");
    fetchAISuggestion(mood);
  };

  const handleCustomMoodSubmit = () => {
    if (customMood.trim() !== "") {
      setSelectedMood(null);
      fetchAISuggestion(customMood);
    }
  };

  return (
    <div className="mood-container">
      <motion.h1
        className="title"
        animate={{ scale: [1, 1.1, 1], opacity: [0, 1] }}
        transition={{ duration: 1, ease: "easeInOut" }}
      >
        How are you feeling today?
      </motion.h1>

      <div className="mood-options">
        {moods.map((mood, index) => (
          <motion.button
            key={index}
            className={`mood-button ${selectedMood === mood.label ? "selected" : ""}`}
            onClick={() => handleMoodSelection(mood.label)}
            whileHover={{ scale: 1.2 }}
            whileTap={{ scale: 0.9 }}
            disabled={loading}
          >
            {mood.emoji}
          </motion.button>
        ))}
      </div>

      <input
        type="text"
        placeholder="Or type your mood..."
        value={customMood}
        onChange={(e) => setCustomMood(e.target.value)}
        className="mood-input"
        disabled={loading}
      />

      <motion.button
        className="submit-button"
        whileHover={{ scale: 1.1 }}
        whileTap={{ scale: 0.9 }}
        onClick={handleCustomMoodSubmit}
        disabled={loading || customMood.trim() === ""}
      >
        {loading ? "Fetching..." : "Submit Mood"}
      </motion.button>

      {error && (
        <motion.div
          className="error-message"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          ❌ {error}
        </motion.div>
      )}

      {aiSuggestion && (
        <motion.div
          className="ai-suggestion"
          initial={{ opacity: 0, y: -10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <strong>AI Suggestion:</strong> {aiSuggestion}
        </motion.div>
      )}

      <p className="quote">
        "Every day may not be good, but there's something good in every day." 💙
      </p>
    </div>
  );
}
