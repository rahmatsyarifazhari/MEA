import "../App.css";
import { Icon } from "@iconify/react";
import { useState, useEffect } from "react";
import socketIOClient from "socket.io-client";

const LiveMonitoring = ({ setPage }) => {
  const [currentCctv, setCurrentCctv] = useState();

  const cctvData = [{ id: 1, name: "GMO - Post Dumping" }];

  const [notificationData, setNotificationData] = useState([]);

  //socket.io
  const socket = socketIOClient("http://10.10.10.66:5000/", {
    transports: ["polling"],
    cors: {
      origin: "*",
    },
  });

  useEffect(() => {
    socket.on("message_from_server", (data) => newNotifHandler(data));
    console.log(socket);

    return () => {
      socket.off("message_from_server");
    };
  }, []);

  const newNotifHandler = (newNotif) => {
    newNotif.map((notification) => {
      setNotificationData((data) => [notification, ...data]);
      console.log(notification);
    });
  };

  const fullscreenHandler = (event) => {
    if (event === "realtime-cctv") {
      document.getElementById(event)?.requestFullscreen();
    } else {
      document.getElementById(event)?.requestFullscreen();
    }
  };

  const cctvArray = cctvData.map((cctv) => {
    return (
      <button
        key={cctv.id}
        className="border-0 text-start rounded-2 px-3 py-2 active"
        onClick={() => {
          setCurrentCctv(cctv);
        }}
      >
        {cctv.name}
      </button>
    );
  });

  const notificationArray = notificationData.map((notification) => {
    return (
      <div>
        <button
          key={notification.id}
          className="border-0 text-start rounded-2 px-3 py-2 d-grid gap-2 w-100"
        >
          <div className="row align-items-center">
            <div className="col-5">
              <label>{"Deviasi " + notification.type_object}</label>
            </div>
          </div>
          <div className="d-flex align-items-end gap-2">
            <Icon className="icon" icon="mdi:cctv" />
            <label>{cctvData[0].name}</label>
          </div>
          <div className="d-flex align-items-end gap-2">
            <Icon className="icon" icon="akar-icons:clock" />
            <label>{notification.time}</label>
          </div>
          <div className="d-flex align-items-end gap-2">
            <label>{"Count: " + notification.count}</label>
          </div>
        </button>
      </div>
    );
  });

  return (
    <div className="live-monitoring">
      <nav className="navbar navbar-expand-lg">
        <div className="container-fluid container">
          <a className="navbar-brand d-flex align-items-center">
            <img src={require("../assets/logo.webp")} alt="logo" />
          </a>
          <button
            className="navbar-toggler"
            type="button"
            data-bs-toggle="collapse"
            data-bs-target="#navbarSupportedContent"
            aria-controls="navbarSupportedContent"
            aria-expanded="false"
            aria-label="Toggle navigation"
          >
            <span className="navbar-toggler-icon"></span>
          </button>
          <div className="collapse navbar-collapse" id="navbarSupportedContent">
            <ul className="navbar-nav ms-auto mb-2 mb-lg-0 gap-2">
              <li className="nav-item d-flex align-items-center">
                <a className="nav-link active">Live Monitoring</a>
              </li>
              <li className="nav-item dropdown">
                <button
                  className="nav-link dropdown-toggle border-0 bg-transparent px-0"
                  data-bs-toggle="dropdown"
                  aria-expanded="false"
                >
                  <Icon className="icon" icon="bi:person-circle" />
                </button>
                <ul className="dropdown-menu dropdown-menu-end mt-2">
                  <li>
                    <label
                      className="dropdown-item disabled text-center"
                      href="#"
                    >
                      {localStorage.getItem("name")}
                    </label>
                  </li>
                  <li>
                    <hr className="dropdown-divider" />
                  </li>
                  <li>
                    <button
                      className="log-out dropdown-item d-flex align-items-center gap-2"
                      onClick={() => {
                        setPage("login");
                        window.localStorage.setItem("page", "login");
                      }}
                    >
                      <Icon className="fs-5" icon="heroicons-outline:logout" />
                      <label>Log Out</label>
                    </button>
                  </li>
                </ul>
              </li>
            </ul>
          </div>
        </div>
      </nav>
      <div className="container mt-3">
        <div className="row">
          <div className="col-xl mb-xl-0 mb-5">
            <div className="row">
              <div className="col-xl-4 mb-xl-0 mb-5">
                <div className="title mb-3">
                  <h6>List CCTV</h6>
                  <label>Pilih CCTV untuk melihat Live Monitoring</label>
                </div>
                <div className="content">
                  <div className="cctv-list d-grid gap-2">{cctvArray}</div>
                </div>
              </div>
              <div className="col-xl">
                <div className="title mb-3">
                  <h6>Real-Time Monitoring</h6>
                  <label>
                    Monitoring deviasi yang terdeteksi secara real-time melalui
                    CCTV Mining Eyes
                  </label>
                </div>
                <div className="content d-grid">
                  <div className="live-cctv d-flex justify-content-center align-items-center rounded-top">
                    <img
                      className="mw-100"
                      src="http://10.10.10.66:5000/video_feed"
                      alt=""
                    />
                  </div>
                  <div className="cam-navigation mb-3 m-0 p-0 align-items-center">
                    <div className="d-flex justify-content-end gap-1">
                      <button
                        className="border-0"
                        title="full-screen"
                        onClick={() => {
                          fullscreenHandler("realtime-cctv");
                        }}
                      >
                        <Icon icon="ic:outline-zoom-out-map" />
                      </button>
                    </div>
                  </div>
                  <div>
                    <div className="cctv-info">
                      <h6>CCTV - Lokasi</h6>
                    </div>
                  </div>
                </div>
              </div>
            </div>
            <div className="visually-hidden">
              <div id="realtime-cctv">
                <img
                  className="w-100"
                  src={
                    "http://10.10.10.66:5002/api/video_feed/" + currentCctv?.id
                  }
                  alt=""
                />
              </div>
            </div>
          </div>
          <div className="col-xl-3">
            <div className="title mb-3">
              <div className="row align-items-center">
                <div className="col-8">
                  <h6>List Notifikasi</h6>
                  <label>List notifikasi deviasi</label>
                </div>
              </div>
            </div>
            <div className="content">
              <div className="notification-list d-grid gap-2 overflow-auto">
                {notificationData.length !== 0 ? (
                  notificationArray
                ) : (
                  <div className="d-flex justify-content-center">
                    <label className="data-not-found">
                      Data tidak ditemukan
                    </label>
                  </div>
                )}
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default LiveMonitoring;
