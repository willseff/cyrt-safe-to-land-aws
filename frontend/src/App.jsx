import { useState } from "react";

const API_BASE = import.meta.env.VITE_API_URL || "";

export default function App() {
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handlePredict = async () => {
    setLoading(true);
    setResult(null);
    setError(null);

    try {
      const res = await fetch(`${API_BASE}/predict`, { method: "POST" });
      const data = await res.json();

      if (res.ok && data.status === "ok") {
        setResult(data.landing_probability);
      } else {
        setError(data.message || "Unknown error");
      }
    } catch (err) {
      setError(err.message || "Failed to reach the server");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={styles.wrapper}>
      <h1 style={styles.title}>Cyrt Safe-to-Land</h1>
      <p style={styles.subtitle}>Weather landing probability predictor</p>

      <button
        onClick={handlePredict}
        disabled={loading}
        style={{
          ...styles.button,
          ...(loading ? styles.buttonDisabled : {}),
        }}
      >
        {loading ? "Running model..." : "Predict Landing"}
      </button>

      {result !== null && (
        <div style={styles.result}>
          <span style={styles.label}>Landing probability:</span>{" "}
          <span style={styles.value}>{(result * 100).toFixed(2)}%</span>
        </div>
      )}

      {error && <div style={styles.error}>{error}</div>}
    </div>
  );
}

const styles = {
  wrapper: {
    fontFamily: "-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif",
    display: "flex",
    flexDirection: "column",
    alignItems: "center",
    justifyContent: "center",
    minHeight: "100vh",
    margin: 0,
    padding: 24,
    background: "#f0f4f8",
    textAlign: "center",
  },
  title: {
    fontSize: "2rem",
    fontWeight: 700,
    color: "#1a202c",
    marginBottom: 8,
  },
  subtitle: {
    fontSize: "1rem",
    color: "#4a5568",
    marginBottom: 32,
  },
  button: {
    padding: "14px 36px",
    fontSize: "1.1rem",
    fontWeight: 600,
    border: "none",
    borderRadius: 8,
    cursor: "pointer",
    background: "#3182ce",
    color: "#fff",
    transition: "background 0.2s",
    marginBottom: 24,
  },
  buttonDisabled: {
    background: "#a0aec0",
    cursor: "not-allowed",
  },
  result: {
    padding: "16px 24px",
    background: "#fff",
    borderRadius: 8,
    boxShadow: "0 2px 8px rgba(0,0,0,0.1)",
    fontSize: "1.2rem",
  },
  label: {
    color: "#4a5568",
  },
  value: {
    fontWeight: 700,
    color: "#2b6cb0",
  },
  error: {
    padding: "12px 20px",
    background: "#fff5f5",
    color: "#c53030",
    borderRadius: 8,
    border: "1px solid #feb2b2",
    maxWidth: 400,
  },
};
