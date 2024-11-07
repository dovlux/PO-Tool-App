import { useState } from "react";
import { Button, CircularProgress, Stack } from "@mui/material";
import UpdateIcon from '@mui/icons-material/Update';
import sendRequest from "../utils/sendRequest";

export default function UpdateCacheButton({ row, fetchCacheStatus, addSnackbar }) {
  const [updatingCache, setUpdatingCache] = useState(false);

  const updateCache = async (name) => {
    setUpdatingCache(true);
    try {
      let response = await sendRequest(
        `dev/cache/${name}/update`, null, 'GET'
      );
      fetchCacheStatus();
      addSnackbar(response.message);
    } catch (error) {
      addSnackbar(error.message, false);
    } finally {
      setUpdatingCache(false);
    }
  }

  return (
    (row.status !== "Updating...") &&
    <Stack alignContent='center' m={1}>
      <Button
        disabled={updatingCache}
        onClick={() => updateCache(row.name.replace("_", "-"))}
      >
        {updatingCache ? <CircularProgress size={24} /> : <UpdateIcon color="primary" />}
      </Button>
    </Stack>
  )
}