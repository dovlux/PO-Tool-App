import { IconButton } from "@mui/material";
import sendRequest from "./sendRequest";
import { ReactComponent as GoogleSheetsIcon } from '../icons/google-sheets-icon.svg';
import RowButtons from "../components/RowButtons";

export async function getPurchaseOrders(roles) {
  const columns = [
    { field: 'id', type: 'number', headerName: 'ID', width: 70, sortable: true },
    { field: 'is_ats', headerName: 'Type', width: 70, valueGetter: (value) => value ? "ATS" : "LUX" },
    { field: 'name', headerName: 'Name', width: 200 },
    { field: 'date_created', type: 'date', headerName: 'Date Created', width: 150,
      valueGetter: (value) => new Date(JSON.parse(value)),
    },
    { field: 'status', headerName: 'Status', width: 200},
    ...(roles.includes('buyer') || roles.includes('admin') ? [
      {
        field: 'actions',
        headerName: 'Actions',
        width: 300,
        sortable: false,
        headerAlign: 'center',
        renderCell: (params) => <RowButtons row={params.row} />
      }
    ] : []),
    { field: 'spreadsheet_id', headerName: '', width: 70, sortable: false, renderCell: (params) => {
        if (!params.value) {
          return null;
        }
        return (
          <IconButton
            component="a"
            href={'https://docs.google.com/spreadsheets/d/' + params.value}
            target="_blank"
            rel="noopener noreferrer"
            aria-label="open google sheet"
          >
            <GoogleSheetsIcon style={{ height: '24px', width: '24px' }} />
          </IconButton>
        );
      }
    }
  ];

  let data = await sendRequest('purchase-orders');
  console.log({ pos: data })
  let rows = data;

  return {
    columns: columns,
    rows: rows,
  }
}