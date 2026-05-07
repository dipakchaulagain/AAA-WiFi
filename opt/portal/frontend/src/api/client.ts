import axios from "axios";

export const api = axios.create({
  baseURL: "/api/v1",
  withCredentials: true,
});

api.interceptors.response.use(
  (r) => r,
  (err) => {
    const status = err?.response?.status;
    if (status === 401 && window.location.pathname !== "/login") {
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

