import React, { Fragment, useState } from "react";
import {
  Stack, List, ListItem, ListItemButton, ListItemText,
  Toolbar, IconButton, Drawer
} from '@mui/material';
import { Link } from 'react-router-dom';
import MenuIcon from '@mui/icons-material/Menu';

const mainMenuItems = [
  { text: 'Purchase Orders', page: 'purchase-orders' },
];

const bottomMenuItems = (roles) => {
  return [
    ...(roles.includes("admin") ? [{ text: 'Settings', page: 'settings' }] : []),
    { text: 'Instructions', page: 'instructions' },
    ...(roles.includes("developer") ? [{ text: 'Developer Settings', page: 'developer' }] : []),
  ]
};

const MenuContent = ( { roles, closeDrawer }) => {
  return (
    <Stack sx={{ flexGrow: 1, pt: 1, flexDirection: 'column', justifyContent: 'space-between' }}>
      <List dense>
        {mainMenuItems.map((item, index) => (
          <ListItem key={index} disablePadding sx={{ display: 'block' }}>
            <ListItemButton component={Link} to={item.page} onClick={closeDrawer}>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>

      <List dense>
        {bottomMenuItems(roles).map((item, index) => (
          <ListItem key={index} disablePadding sx={{ display: 'block' }}>
            <ListItemButton component={Link} to={item.page} onClick={closeDrawer}>
              <ListItemText primary={item.text} />
            </ListItemButton>
          </ListItem>
        ))}
      </List>
    </Stack>
  )
}

export default function SideBar({ roles }) {
  const [open, setOpen] = useState(false);

  const openDrawer = () => {
    setOpen(true);
  }

  const closeDrawer = () => {
    setOpen(false);
  }

  return (
    <Fragment>
      <IconButton
        color="inherit"
        aria-label="open drawer"
        onClick={openDrawer}
        edge="start"
        sx={[
          { mr: 2, },
          open && { display: 'none' },
        ]}
      >
        <MenuIcon />
      </IconButton>
      <Drawer open={open} onClose={closeDrawer}>
        <Toolbar />
        <MenuContent roles={roles} closeDrawer={closeDrawer}/>
      </Drawer>
    </Fragment>
  )
}