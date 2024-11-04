import { Stack } from "@mui/material";
import { useState } from "react";
import DeletePoDialog from "./DeletePoDialog";
import CreateBreakdownDialog from "./CreateBreakdownDialog";
import CalculateNetSalesDialog from "./CalculateNetSalesDialog";
import CreateSkusAndPoDialog from "./CreateSkusAndPoDialog";
import UndoDialog from "./UndoDialog";

export default function ActionRowButtons ({ row, addSnackbar, fetchPos }) {
  const [buttonLoading, setButtonLoading] = useState(false);

  return (
    <Stack direction='row' alignContent='center' spacing={1} m={1}>
      {(
        row.is_ats === false &&
        (
          row.status === "Worksheet Created" ||
          row.status === "Errors in worksheet (Breakdown)"
        )
      ) && (
        <CreateBreakdownDialog
          buttonLoading={buttonLoading}
          setButtonLoading={setButtonLoading}
          id={row.id}
          addSnackbar={addSnackbar}
          fetchPos={fetchPos}
        />
      )}
      {(
        row.is_ats === false &&
        (
          row.status === "Breakdown Created" ||
          row.status === "Errors in worksheet (Net Sales)"
        )
      ) && (
        <CalculateNetSalesDialog
          buttonLoading={buttonLoading}
          setButtonLoading={setButtonLoading}
          id={row.id}
          addSnackbar={addSnackbar}
          fetchPos={fetchPos}
        />
      )}
      {(
        row.status === "Errors in worksheet (Create SKUs and PO)" ||
        (row.is_ats === true && row.status === "Worksheet Created") ||
        (row.is_ats === false && row.status === "Net Sales Calculated")
      ) && (
        <CreateSkusAndPoDialog
          buttonLoading={buttonLoading}
          setButtonLoading={setButtonLoading}
          id={row.id}
          addSnackbar={addSnackbar}
          fetchPos={fetchPos}
        />
      )}
      {(
        row.status === "Worksheet Created" || row.status === "Errors in worksheet (Breakdown)" ||
        row.status === "Errors in worksheet (Create SKUs and PO)"
      ) && (
        <DeletePoDialog
          buttonLoading={buttonLoading}
          setButtonLoading={setButtonLoading}
          id={row.id}
          addSnackbar={addSnackbar}
          fetchPos={fetchPos}
        />
      )}
      {(
        row.is_ats === false &&
        (
          row.status === "Breakdown Created" || row.status === "Errors in worksheet (Net Sales)" ||
          row.status === "Net Sales Calculated"
        )
      ) && (
        <UndoDialog
          buttonLoading={buttonLoading}
          setButtonLoading={setButtonLoading}
          id={row.id}
          status={row.status}
          addSnackbar={addSnackbar}
          fetchPos={fetchPos}
        />
      )}
    </Stack>
  )
}