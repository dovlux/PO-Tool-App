import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from './components/Layout';
import PurchaseOrders from './pages/PurchaseOrders';
import Settings from './pages/Settings';
import Instructions from './pages/Instructions';
import Developer from './pages/Developer';

const App = () => {
	return (
		<Router>
			<Routes>
				<Route path="/" element={<Layout />}>
					<Route index element={<PurchaseOrders />} />
					<Route path="purchase-orders" element={<PurchaseOrders />} />
					<Route path="settings" element={<Settings />} />
					<Route path="instructions" element={<Instructions />} />
					<Route path="developer" element={<Developer />} />
				</Route>
			</Routes>
		</Router>
	);
};

export default App;
