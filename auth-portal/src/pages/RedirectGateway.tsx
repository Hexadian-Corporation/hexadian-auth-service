import { useEffect } from "react";
import { Navigate } from "react-router";
import { parseAccessToken } from "@/lib/auth";
import { getPortalRedirect } from "@/api/settings";

export default function RedirectGateway() {
  const tokenPayload = parseAccessToken();

  useEffect(() => {
    if (!tokenPayload?.rsi_verified) return;

    getPortalRedirect().then(({ default_redirect_url }) => {
      window.location.href = default_redirect_url;
    });
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  if (!tokenPayload) {
    return <Navigate to="/login" replace />;
  }

  if (!tokenPayload.rsi_verified) {
    return <Navigate to="/verify" replace />;
  }

  return null;
}
