import React, { useState, useEffect } from 'react';
import {
  Box,
  Popover,
  Typography,
  Avatar,
  IconButton,
  Button,
  Divider
} from '@mui/material';

interface Notification {
  id: number;
  user_id: number;
  pcr_id: number;
  type: string;
  title: string;
  message: string | null;
  is_read: number;
  created_at: string;
  product_name?: string;
  pcr_status?: string;
  pcr_id_display?: string | null;
}

interface NotificationPopoverProps {
  anchorEl: HTMLElement | null;
  onClose: () => void;
  userId?: number;
}

const NotificationPopover: React.FC<NotificationPopoverProps> = ({ 
  anchorEl, 
  onClose,
  userId 
}) => {
  const [notifications, setNotifications] = useState<Notification[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (userId && anchorEl) {
      fetchNotifications();
    }
  }, [userId, anchorEl]);

  const fetchNotifications = async () => {
    if (!userId) return;
    try {
      setLoading(true);
      const response = await fetch(`/api/users/${userId}/notifications`);
      if (response.ok) {
        const data = await response.json();
        setNotifications(data.notifications || []);
      }
    } catch (err) {
      console.error('Failed to load notifications:', err);
    } finally {
      setLoading(false);
    }
  };

  const formatTime = (dateString: string): string => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffDays = Math.floor(diffMs / (1000 * 60 * 60 * 24));
    const diffHours = Math.floor(diffMs / (1000 * 60 * 60));
    const diffMinutes = Math.floor(diffMs / (1000 * 60));
    
    if (diffMinutes < 1) return 'just now';
    if (diffMinutes < 60) return `${diffMinutes} minute${diffMinutes > 1 ? 's' : ''} ago`;
    if (diffHours < 24) return `${diffHours} hour${diffHours > 1 ? 's' : ''} ago`;
    if (diffDays === 1) return 'a day ago';
    if (diffDays < 7) return `${diffDays} days ago`;
    
    return date.toLocaleDateString('en-GB', {
      day: '2-digit',
      month: 'short',
      year: 'numeric',
      hour: 'numeric',
      minute: '2-digit'
    });
  };

  const handleMarkAllAsRead = async () => {
    if (!userId) return;
    try {
      const response = await fetch(`/api/users/${userId}/notifications/read-all`, {
        method: 'PUT',
      });
      if (response.ok) {
        setNotifications(prev => prev.map(n => ({ ...n, is_read: 1 })));
      }
    } catch (err) {
      console.error('Failed to mark all as read:', err);
    }
  };

  const handleNotificationClick = async (notification: Notification) => {
    if (notification.is_read === 0) {
      try {
        const response = await fetch(`/api/notifications/${notification.id}/read`, {
          method: 'PUT',
        });
        if (response.ok) {
          setNotifications(prev => 
            prev.map(n => n.id === notification.id ? { ...n, is_read: 1 } : n)
          );
        }
      } catch (err) {
        console.error('Failed to mark as read:', err);
      }
    }
    // TODO: Navigate to PCR detail page
    console.log('Navigate to PCR:', notification.pcr_id);
    onClose();
  };

  const open = Boolean(anchorEl);

  return (
    <Popover
      open={open}
      anchorEl={anchorEl}
      onClose={onClose}
      anchorOrigin={{
        vertical: 'bottom',
        horizontal: 'right',
      }}
      transformOrigin={{
        vertical: 'top',
        horizontal: 'right',
      }}
      PaperProps={{
        sx: {
          width: 450,
          maxWidth: '90vw',
          maxHeight: '80vh',
          mt: 1,
          boxShadow: '0 4px 20px rgba(0,0,0,0.15)',
          borderRadius: 2
        }
      }}
    >
      {/* Header */}
      <Box
        sx={{
          p: 2,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          borderBottom: '1px solid #e0e0e0',
        }}
      >
        <Typography variant="h6" sx={{ fontWeight: 600, color: '#333' }}>
          Notifications
        </Typography>

        <Button
          onClick={handleMarkAllAsRead}
          sx={{
            textTransform: 'none',
            color: '#1976d2',
            fontSize: '0.85rem',
            fontWeight: 500,
            '&:hover': {
              bgcolor: 'transparent',
              textDecoration: 'underline'
            }
          }}
        >
          Mark all as read
        </Button>
      </Box>

      {/* Notifications List */}
      <Box sx={{ maxHeight: 'calc(80vh - 80px)', overflowY: 'auto' }}>
        {loading ? (
          <Box sx={{ p: 6, textAlign: 'center' }}>
            <Typography variant="body2" color="text.secondary">
              Loading...
            </Typography>
          </Box>
        ) : notifications.length === 0 ? (
          <Box sx={{ p: 6, textAlign: 'center' }}>
            <Typography variant="h6" color="text.secondary">
              No notifications
            </Typography>
            <Typography variant="body2" color="text.secondary" sx={{ mt: 1 }}>
              You're all caught up!
            </Typography>
          </Box>
        ) : (
          notifications.map((notification, index) => (
            <React.Fragment key={notification.id}>
              <Box
                onClick={() => handleNotificationClick(notification)}
                sx={{
                  display: 'flex',
                  gap: 2,
                  p: 2,
                  cursor: 'pointer',
                  bgcolor: notification.is_read === 0 ? '#f8f9ff' : 'transparent',
                  '&:hover': {
                    bgcolor: notification.is_read === 0 ? '#f0f1ff' : '#f8f9fa'
                  },
                  position: 'relative'
                }}
              >
                {/* Icon/Avatar */}
                <Avatar
                  sx={{
                    bgcolor: '#5e6c84',
                    width: 36,
                    height: 36,
                    flexShrink: 0
                  }}
                >
                  <Box
                    component="img"
                    src="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='white'%3E%3Cpath d='M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z'/%3E%3C/svg%3E"
                    sx={{ width: 20, height: 20 }}
                  />
                </Avatar>

                {/* Content */}
                <Box sx={{ flex: 1, minWidth: 0 }}>
                  <Typography
                    variant="body2"
                    sx={{
                      fontWeight: notification.is_read === 0 ? 600 : 400,
                      color: '#172b4d',
                      mb: 0.5,
                      fontSize: '0.9rem',
                      lineHeight: 1.4
                    }}
                  >
                    {notification.title}
                  </Typography>

                  <Typography
                    variant="body2"
                    sx={{
                      color: '#5e6c84',
                      fontSize: '0.8rem',
                      mb: 0.75,
                      lineHeight: 1.4,
                      overflow: 'hidden',
                      textOverflow: 'ellipsis',
                      display: '-webkit-box',
                      WebkitLineClamp: 2,
                      WebkitBoxOrient: 'vertical'
                    }}
                  >
                    {notification.pcr_id_display
                      ? `${notification.pcr_id_display} • ${notification.message ?? ''}`
                      : (notification.message ?? '')}
                  </Typography>

                  <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <Typography
                      variant="caption"
                      sx={{
                        color: '#8993a4',
                        fontSize: '0.75rem'
                      }}
                    >
                      {formatTime(notification.created_at)}
                    </Typography>
                    {notification.is_read === 0 && (
                      <Box
                        sx={{
                          width: 6,
                          height: 6,
                          borderRadius: '50%',
                          bgcolor: '#1976d2'
                        }}
                      />
                    )}
                  </Box>
                </Box>
              </Box>
              {index < notifications.length - 1 && <Divider />}
            </React.Fragment>
          ))
        )}
      </Box>
    </Popover>
  );
};

export default NotificationPopover;