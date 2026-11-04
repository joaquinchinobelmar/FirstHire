import { Navigate, Route, Routes } from "react-router-dom";
import { Briefcase, ClipboardList, IdCard, Lightbulb, Users } from "lucide-react";
import type { ReactNode } from "react";
import { AppShell } from "./components/AppShell";
import { Spinner } from "./components/ui";
import { homeFor, useAuth } from "./lib/auth";
import type { Role } from "./lib/types";
import Landing from "./pages/Landing";
import Login from "./pages/Login";
import Trust from "./pages/Trust";
import Profile from "./pages/graduate/Profile";
import Opportunities from "./pages/graduate/Opportunities";
import Applications from "./pages/graduate/Applications";
import Advisor from "./pages/owner/Advisor";
import Applicants from "./pages/owner/Applicants";

function RequireRole({ role, children }: { role: Role; children: ReactNode }) {
  const { user, loading } = useAuth();
  if (loading) return <Spinner label="Loading…" />;
  if (!user) return <Navigate to="/login" replace />;
  if (user.role !== role) return <Navigate to={homeFor(user.role)} replace />;
  return <>{children}</>;
}

const GRAD_TABS = [
  { to: "/graduate/profile", label: "My Passport", icon: <IdCard className="size-4" /> },
  { to: "/graduate/opportunities", label: "Opportunities", icon: <Briefcase className="size-4" /> },
  { to: "/graduate/applications", label: "Applications", icon: <ClipboardList className="size-4" /> },
];
const OWNER_TABS = [
  { to: "/business/advisor", label: "Growth Advisor", icon: <Lightbulb className="size-4" /> },
  { to: "/business/applicants", label: "Applicants", icon: <Users className="size-4" /> },
];

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/login" element={<Login />} />
      <Route path="/trust" element={<Trust />} />
      <Route path="/graduate" element={<RequireRole role="graduate"><AppShell tabs={GRAD_TABS} areaLabel="Graduate" /></RequireRole>}>
        <Route index element={<Navigate to="profile" replace />} />
        <Route path="profile" element={<Profile />} />
        <Route path="opportunities" element={<Opportunities />} />
        <Route path="applications" element={<Applications />} />
      </Route>
      <Route path="/business" element={<RequireRole role="owner"><AppShell tabs={OWNER_TABS} areaLabel="Business" /></RequireRole>}>
        <Route index element={<Navigate to="advisor" replace />} />
        <Route path="advisor" element={<Advisor />} />
        <Route path="applicants" element={<Applicants />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
