import React, { useState, useCallback } from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import PurchaseOrders from './pages/PurchaseOrders';
import Settings from './pages/Settings';
import Instructions from './pages/Instructions';
import Developer from './pages/Developer';

const App = () => {
	const [loading, setLoading] = useState(false);
  const [snackbars, setSnackbars] = useState([]);

  const addSnackbar = useCallback((message, isSuccess = true, ms = 10) => {
    setSnackbars((prev) => [
      {
				id: new Date().getTime(),
				message: message,
				severity: isSuccess ? 'success' : 'error', ms: ms * 1000
			},
      ...prev,
    ])
  }, []);

	return (
		<Router>
			<Routes>
				<Route path="/" element={<Layout loading={loading} snackbars={snackbars} setSnackbars={setSnackbars} />}>
					<Route index element={<PurchaseOrders setLoading={setLoading} addSnackbar={addSnackbar} />} />
					<Route path="purchase-orders" element={<PurchaseOrders setLoading={setLoading} addSnackbar={addSnackbar} />} />
					<Route path="settings" element={<Settings />} />
					<Route path="instructions" element={<Instructions />} />
					<Route path="developer" element={<Developer setLoading={setLoading} addSnackbar={addSnackbar} />} />
				</Route>
			</Routes>
		</Router>
	);
};

export default App;
