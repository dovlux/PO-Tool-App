import React, { createContext, useState, useContext, useEffect, useCallback, useMemo } from 'react';
import { getPurchaseOrders } from '../utils/getPurchaseOrders';
import { getCacheStatus } from '../utils/getCacheStatus';
import { useLocation } from 'react-router-dom';

const Context = createContext();

export const ContextProvider = ({ children }) => {
  const roles = useMemo(() => ["admin"], []);
  const [loading, setLoading] = useState(false);
  const [snackbars, setSnackbars] = useState([]);
  const [poRows, setPoRows] = useState([]);
  const [poColumns, setPoColumns] = useState([]);
  const [cacheRows, setCacheRows] = useState([]);
  const [cacheColumns, setCacheColumns] = useState([]);
  const location = useLocation();

  const addSnackbar = useCallback((message, isSuccess = true, ms = 10) => {
    setSnackbars((prev) => [
      {id: new Date().getTime(), message: message, severity: isSuccess ? 'success' : 'error', ms: ms * 1000},
      ...prev,
    ])
  }, []);

  const fetchCacheStatus = useCallback(async (background) => {
    if (!background) setLoading(true);
    try {
      let caches = await getCacheStatus();
      setCacheRows(caches.rows);
      setCacheColumns(caches.columns);
    } catch (error) {
      if (!background) addSnackbar(error.message);
    } finally {
      if (!background) setLoading(false);
    }
  }, [addSnackbar]);

  useEffect(() => {
    if (location.pathname === '/developer' && roles.includes('developer')) {
      fetchCacheStatus(false);
      const intervalId = setInterval(fetchCacheStatus(true), 15000);
      return () => clearInterval(intervalId);
    }
  }, [fetchCacheStatus, location, roles]);

  const fetchPos = useCallback(async (background) => {
    if (!background) setLoading(true);
    try {
      let pos = await getPurchaseOrders(roles);
      setPoRows(pos.rows);
      setPoColumns(pos.columns);
    } catch (error) {
      if (!background) addSnackbar(error.message, false);
    } finally {
      if (!background) setLoading(false);
    }
  }, [roles, addSnackbar]);

  useEffect(() => {
    if (location.pathname === '/purchase-orders') {
      fetchPos(false);
      const intervalId = setInterval(fetchPos(true), 15000);
      return () => clearInterval(intervalId);
    }
  }, [fetchPos, location]);

  return (
    <Context.Provider
      value={{
        roles, loading, setLoading, snackbars, setSnackbars, addSnackbar, poRows, poColumns,
        fetchPos, cacheRows, cacheColumns, fetchCacheStatus,
      }}
    >
      {children}
    </Context.Provider>
  );
};

export const useAllContext = () => {
  return useContext(Context);
}