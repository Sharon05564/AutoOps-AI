import { Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import IncidentDetail from "./pages/IncidentDetail";
import Incidents from "./pages/Incidents";
import Overview from "./pages/Overview";
import Postmortem from "./pages/Postmortem";
import Services from "./pages/Services";

function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<Overview />} />
        <Route path="incidents" element={<Incidents />} />
        <Route path="incidents/:incidentId" element={<IncidentDetail />} />
        <Route path="incidents/:incidentId/postmortem" element={<Postmortem />} />
        <Route path="services" element={<Services />} />
      </Route>
    </Routes>
  );
}

export default App;
