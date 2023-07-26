import "./App.css";
import Login from "./components/Login";
import LiveMonitoring from "./components/LiveMonitoring";
import { useState } from "react";

function App() {
  const [page, setPage] = useState(
    window.localStorage.getItem("page") === "login"
      ? "login"
      : "live-monitoring"
  );

  return (
    <div className="App">
      {page === "login" ? (
        <Login setPage={setPage} />
      ) : (
        <LiveMonitoring setPage={setPage} />
      )}
    </div>
  );
}

export default App;
