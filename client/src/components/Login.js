import "../App.css";
import { useState } from "react";
import { Icon } from "@iconify/react";

const Login = ({ setPage }) => {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [passwordVisibility, setPasswordVisibility] = useState(false);
  const [loginMessage, setLoginMessage] = useState("");

  const enterKeyHandler = () => {};

  const loginHandler = () => {
    if (username === "" || password === "") {
      setLoginMessage("username dan password tidak boleh kosong");
    } else {
      window.localStorage.setItem("name", username);
      setPage("live-monitoring");
      window.localStorage.setItem("page", "live-monitoring");
    }
  };

  return (
    <div className="login d-flex justify-content-center align-items-center">
      <div className="form-container rounded-4">
        <div className="d-flex justify-content-center align-items-center pt-3 p-0">
          <div className="login-container">
            <h3>Log in</h3>
            <p>
              Selamat Datang kembali! Silahkan isi beberapa detail di bawah ini.
            </p>
            <form className="my-4 d-grid gap-2">
              <div className="d-grid gap-1">
                <label>Username/ SID</label>
                <input
                  type="text"
                  className="form-control"
                  placeholder="Masukkan Username atau SID"
                  onChange={(e) => setUsername(e.target.value)}
                  onKeyDown={(e) => {
                    e.key === "Enter" ? loginHandler() : enterKeyHandler();
                  }}
                />
              </div>
              <div className="d-grid gap-1">
                <label>Password</label>
                <div className="d-flex align-items-center">
                  <input
                    type={passwordVisibility === false ? "password" : "text"}
                    className="form-control"
                    placeholder="Masukkan Password"
                    onChange={(e) => setPassword(e.target.value)}
                    onKeyDown={(e) => {
                      e.key === "Enter" ? loginHandler() : enterKeyHandler();
                    }}
                  />
                  <Icon
                    className="password-visibility"
                    icon={
                      passwordVisibility === false
                        ? "clarity:eye-line"
                        : "clarity:eye-hide-line"
                    }
                    onClick={() => {
                      setPasswordVisibility(!passwordVisibility);
                    }}
                  />
                </div>
              </div>
            </form>
            <div className="d-grid">
              <button
                className="border-0 rounded-2 px-3 py-2"
                onClick={loginHandler}
              >
                Masuk
              </button>
            </div>
            <label className="login-message mt-2">
              {loginMessage !== "" ? "*" + loginMessage : ""}
            </label>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Login;
