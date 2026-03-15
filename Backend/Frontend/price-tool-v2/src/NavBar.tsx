import * as React from 'react';
import { styled, alpha } from '@mui/material/styles';
import AppBar from '@mui/material/AppBar';
import Box from '@mui/material/Box';
import Toolbar from '@mui/material/Toolbar';
import IconButton from '@mui/material/IconButton';
import Typography from '@mui/material/Typography';
import InputBase from '@mui/material/InputBase';
import Badge from '@mui/material/Badge';
import MenuItem from '@mui/material/MenuItem';
import Menu from '@mui/material/Menu';
import MenuIcon from '@mui/icons-material/Menu';
import SearchIcon from '@mui/icons-material/Search';
import AccountCircle from '@mui/icons-material/AccountCircle';
import MailIcon from '@mui/icons-material/Mail';
import NotificationsIcon from '@mui/icons-material/Notifications';
import MoreIcon from '@mui/icons-material/MoreVert';
import { LogOut } from 'lucide-react';
import Drawer from '@mui/material/Drawer';
import List from '@mui/material/List';
import ListItem from '@mui/material/ListItem';
import ListItemButton from '@mui/material/ListItemButton';
import ListItemIcon from '@mui/material/ListItemIcon';
import ListItemText from '@mui/material/ListItemText';
import Divider from '@mui/material/Divider';
import HomeIcon from '@mui/icons-material/Home';
import DashboardIcon from '@mui/icons-material/Dashboard';
import SettingsIcon from '@mui/icons-material/Settings';
import InfoIcon from '@mui/icons-material/Info';
import { Link, Navigate } from "react-router-dom";
import LocalOfferIcon from "@mui/icons-material/LocalOffer";
import { useNavigate } from 'react-router-dom';
import { NavLink } from 'react-router-dom';
import NotificationPopover from './NotificationPopover';
import MessagesPopover from './MessagesPopover';



const Search = styled('div')(({ theme }) => ({
  position: 'relative',
  borderRadius: theme.shape.borderRadius,
  backgroundColor: alpha(theme.palette.common.black, 0.08),
  '&:hover': {
    backgroundColor: alpha(theme.palette.common.black, 0.15),
  },
  marginRight: theme.spacing(2),
  marginLeft: 0,
  width: '100%',
  [theme.breakpoints.up('sm')]: {
    marginLeft: theme.spacing(3),
    width: 'auto',
  },
}));

const SearchIconWrapper = styled('div')(({ theme }) => ({
  padding: theme.spacing(0, 2),
  height: '100%',
  position: 'absolute',
  pointerEvents: 'none',
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'center',
}));

const StyledInputBase = styled(InputBase)(({ theme }) => ({
  color: 'inherit',
  '& .MuiInputBase-input': {
    padding: theme.spacing(1, 1, 1, 0),
    paddingLeft: `calc(1em + ${theme.spacing(4)})`,
    transition: theme.transitions.create('width'),
    width: '100%',
    [theme.breakpoints.up('md')]: {
      width: '20ch',
    },
  },
}));

interface NavBarProps {
  onLogout: () => void;

  loggedInUser: {
    id?: number;
    role: string;
    email: string;
    name?: string;
    phone?: string;
    location?: string;
    joinDate?: string;
  };
}

export default function NavBar({ onLogout, loggedInUser }: NavBarProps) {
  const [anchorEl, setAnchorEl] = React.useState<null | HTMLElement>(null);
  const [mobileMoreAnchorEl, setMobileMoreAnchorEl] =
    React.useState<null | HTMLElement>(null);
  const [drawerOpen, setDrawerOpen] = React.useState(false);
  const [notificationAnchorEl, setNotificationAnchorEl] = React.useState<null | HTMLElement>(null);
  const [messagesAnchorEl, setMessagesAnchorEl] = React.useState<null | HTMLElement>(null);
  const navigate = useNavigate();

  const isMenuOpen = Boolean(anchorEl);
  const isMobileMenuOpen = Boolean(mobileMoreAnchorEl);

  const handleProfileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget);
  };

  const handleMobileMenuClose = () => {
    setMobileMoreAnchorEl(null);
  };

  const handleMenuClose = () => {
    setAnchorEl(null);
    handleMobileMenuClose();
  };

  const handleMobileMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setMobileMoreAnchorEl(event.currentTarget);
  };

  const handleNotificationClick = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchorEl(event.currentTarget);
  };

  const handleNotificationClose = () => {
    setNotificationAnchorEl(null);
  };

  const handleMessagesClick = (event: React.MouseEvent<HTMLElement>) => {
    setMessagesAnchorEl(event.currentTarget);
  };

  const handleMessagesClose = () => {
    setMessagesAnchorEl(null);
  };

  const toggleDrawer = (open: boolean) => (event: React.KeyboardEvent | React.MouseEvent) => {
    if (
      event.type === 'keydown' &&
      ((event as React.KeyboardEvent).key === 'Tab' ||
        (event as React.KeyboardEvent).key === 'Shift')
    ) {
      return;
    }
    setDrawerOpen(open);
  };

  const drawerList = (
    <Box
      sx={{ width: 250 }}
      role="presentation"
      onClick={toggleDrawer(false)}
      onKeyDown={toggleDrawer(false)}
    >
      <Box sx={{ p: 2, bgcolor: 'white', color: 'black' }}>
       
        <Typography variant="h6" sx={{ fontWeight: 'bold', color:'#005B6E' }}>
          <LocalOfferIcon sx={{ color: "#D4AF37"}}  />   
          PRICE-TOOL
        </Typography>
       <Box
  sx={{
    mt: 1,
    pt: 1,
    bgcolor: "secondary.main",
    width: "calc(100% + 32px)",
    ml: "-16px",
    mr: "-16px",
    px: 2,
    color:'white'
  }}
>

          <Typography variant="body2" sx={{ fontWeight: 'bold' }}>
            {loggedInUser.role}
          </Typography>
          <Typography variant="caption" sx={{ display: 'block' }}>
            {loggedInUser.email}
          </Typography>
        </Box>
      </Box>
      <Divider />
      <List>
        <ListItem disablePadding>
          <ListItemButton component={NavLink} to="/Home"  end
      sx={{
        "&.active": {
          backgroundColor: "grey.300",
        },
      }}>
            <ListItemIcon>
              <HomeIcon sx={{color:"black"}} />
            </ListItemIcon>
            <ListItemText primary="Home" />
          </ListItemButton>
        </ListItem>
        <ListItem disablePadding>
          <ListItemButton component={NavLink} to="/Product"    sx={{
        "&.active": {
          backgroundColor: "grey.300",
        },
      }}>
            <ListItemIcon>
              <DashboardIcon sx={{color:"black"}} />
            </ListItemIcon>
            <ListItemText primary="Product" />
          </ListItemButton>
        </ListItem>
        {(loggedInUser?.role === "Admin" || (loggedInUser?.role as string)?.toLowerCase() === "admin") && (
          <ListItem disablePadding>
            <ListItemButton component={NavLink} to="/Home/AdminPage" sx={{
              "&.active": { backgroundColor: "grey.300" },
            }}>
              <ListItemIcon>
                <SettingsIcon sx={{ color: "black" }} />
              </ListItemIcon>
              <ListItemText primary="Admin" />
            </ListItemButton>
          </ListItem>
        )}
        <ListItem disablePadding>
          <ListItemButton    sx={{
        "&.active": {
          backgroundColor: "grey.300",
        },
      }}>
            <ListItemIcon>
              <SettingsIcon sx={{color:"black"}}/>
            </ListItemIcon>
            <ListItemText primary="Settings" />
          </ListItemButton>
        </ListItem>
        <ListItem disablePadding>
          <ListItemButton    sx={{
        "&.active": {
          backgroundColor: "grey.300",
        },
      }}>
            <ListItemIcon>
              <InfoIcon sx={{color:"black"}}/>
            </ListItemIcon>
            <ListItemText primary="About" />
          </ListItemButton>
        </ListItem>
      </List>
      <Divider />
      <List>
        <ListItem disablePadding>
          <ListItemButton onClick={onLogout}>
            <ListItemIcon sx={{color:"black"}}>
              <LogOut size={20} />
            </ListItemIcon>
            <ListItemText primary="Logout" />
          </ListItemButton>
        </ListItem>
      </List>
    </Box>
  );

  const menuId = 'primary-search-account-menu';
  const renderMenu = (
    <Menu
      anchorEl={anchorEl}
      anchorOrigin={{
        vertical: 'top',
        horizontal: 'right',
      }}
      id={menuId}
      keepMounted
      transformOrigin={{
        vertical: 'top',
        horizontal: 'right',
      }}
      open={isMenuOpen}
      onClose={handleMenuClose}
    >
      <MenuItem component={Link} to="/ProfilePage" onClick={handleMenuClose}>Profile</MenuItem>
      <MenuItem onClick={handleMenuClose}>My account</MenuItem>
    </Menu>
  );

  const mobileMenuId = 'primary-search-account-menu-mobile';
  const renderMobileMenu = (
    <Menu
      anchorEl={mobileMoreAnchorEl}
      anchorOrigin={{
        vertical: 'top',
        horizontal: 'right',
      }}
      id={mobileMenuId}
      keepMounted
      transformOrigin={{
        vertical: 'top',
        horizontal: 'right',
      }}
      open={isMobileMenuOpen}
      onClose={handleMobileMenuClose}
    >
      <MenuItem onClick={(e) => {
         handleMobileMenuClose();
         handleMessagesClick(e);
      }}>
        <IconButton size="large" aria-label="show 4 new mails" color="inherit">
          <Badge badgeContent={4} color="error">
            <MailIcon />
          </Badge>
        </IconButton>
        <p>Messages</p>
      </MenuItem>
      <MenuItem onClick={(e) => {
         handleMobileMenuClose();
         handleNotificationClick(e);
      }}>
        <IconButton
          size="large"
          aria-label="show new notifications"
          color="inherit"
         >
         <Badge badgeContent={17} color="error">
           <NotificationsIcon />
         </Badge>
        </IconButton>
          <p>Notifications</p>
       </MenuItem>
      <MenuItem component={Link} to="/ProfilePage" onClick={handleMobileMenuClose}>
        <IconButton
          size="large"
          aria-label="account of current user"
          aria-controls="primary-search-account-menu"
          aria-haspopup="true"
          color="inherit"
        >
          <AccountCircle />
        </IconButton>
        <p>Profile</p>
      </MenuItem>
      <MenuItem onClick={onLogout}>
        <IconButton size="large" color="inherit">
          <LogOut size={20} />
        </IconButton>
        <p>Logout</p>
      </MenuItem>
    </Menu>
  );

  return (
    <Box sx={{ flexGrow: 1, padding: 2 }}>
      <AppBar position="static" sx={{ backgroundColor: 'white', color: 'black', borderRadius: 2, boxShadow: 3 }}>
        <Toolbar>
          <IconButton
            size="large"
            edge="start"
            color="inherit"
            aria-label="open drawer"
            sx={{ mr: 2 }}
            onClick={toggleDrawer(true)}
          >
            <MenuIcon />
          </IconButton>
          <Typography
            variant="h6"
            noWrap
            component="div"
            sx={{ display: { xs: 'none', sm: 'block',color:'#005B6E' }, fontWeight: 'bold' }}
          >
            <LocalOfferIcon sx={{ color: "#D4AF37"}} />
            Price-Tool
          </Typography>
          <Search>
            <SearchIconWrapper>
              <SearchIcon />
            </SearchIconWrapper>
            <StyledInputBase
              placeholder="Search…"
              inputProps={{ 'aria-label': 'search' }}
            />
          </Search>
          <Box sx={{ flexGrow: 1 }} />
          <Box sx={{ display: { xs: 'none', md: 'flex' }, alignItems: 'center' }}>
            <IconButton 
              size="large" 
              aria-label="show 4 new mails" 
              color="inherit"
              onClick={handleMessagesClick}
            >
              <Badge badgeContent={4} color="error">
                <MailIcon />
              </Badge>
            </IconButton>
            <IconButton
             size="large"
             aria-label="show new notifications"
             color="inherit"
             onClick={handleNotificationClick}
             >
             <Badge badgeContent={17} color="error">
              <NotificationsIcon />
             </Badge>
            </IconButton>
            <IconButton
              size="large"
              aria-label="account of current user"
              aria-controls={menuId}
              aria-haspopup="true"
              onClick={handleProfileMenuOpen}
              color="inherit"
            >
            <AccountCircle/>
            </IconButton>
          </Box>
          <Box sx={{ display: { xs: 'flex', md: 'none' } }}>
            <IconButton
              size="large"
              aria-label="show more"
              aria-controls={mobileMenuId}
              aria-haspopup="true"
              onClick={handleMobileMenuOpen}
              color="inherit"
            >
              <MoreIcon />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>
      <Drawer anchor="left" open={drawerOpen} onClose={toggleDrawer(false)}>
        {drawerList}
      </Drawer>
      {renderMobileMenu}
      {renderMenu}
      <NotificationPopover 
        anchorEl={notificationAnchorEl} 
        onClose={handleNotificationClose}
        userId={loggedInUser?.id}
      />
      <MessagesPopover 
        anchorEl={messagesAnchorEl} 
        onClose={handleMessagesClose}
        loggedInUser={loggedInUser}
      />
    </Box>
  );
}