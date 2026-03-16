import { BrowserRouter, Routes, Route, Navigate } from "react-router";
import LoginPage from "@/pages/LoginPage";
import RegisterPage from "@/pages/RegisterPage";
import CallbackPage from "@/pages/CallbackPage";
import VerifyPage from "@/pages/VerifyPage";
import ChangePasswordPage from "@/pages/ChangePasswordPage";

export default function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route path="/register" element={<RegisterPage />} />
        <Route path="/callback" element={<CallbackPage />} />
        <Route path="/verify" element={<VerifyPage />} />
        <Route path="/password/change" element={<ChangePasswordPage />} />
        <Route path="*" element={<Navigate to="/login" replace />} />
      </Routes>
    </BrowserRouter>
  );
}
