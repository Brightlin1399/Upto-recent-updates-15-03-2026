import React from 'react';
import {
  Box,
  List,
  ListItem,
  ListItemButton,
  ListItemAvatar,
  Avatar,
  ListItemText,
  Typography,
  IconButton,
  Divider,
} from '@mui/material';
import CloseIcon from '@mui/icons-material/Close';
import AddIcon from '@mui/icons-material/Add';

export interface Message {
  id: number;
  sender: string;
  preview: string;
  time: string;
  avatarColor: string;
  active?: boolean;
  unread?: boolean;
}

interface MessageListProps {
  messages: Message[];
  onConversationClick: (message: Message) => void;
  onClose: () => void;
  loading?: boolean;
  onNewChat?: () => void;
}

export default function MessageList({ messages, onConversationClick, onClose, loading, onNewChat }: MessageListProps) {
  return (
    <Box>
      <Box sx={{ p: 2, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <Typography variant="h6" sx={{ fontWeight: 'bold' }}>
          Messages
        </Typography>
        <Box sx={{ display: 'flex', gap: 0.5 }}>
          {onNewChat && (
            <IconButton size="small" onClick={onNewChat} title="New chat" aria-label="New chat">
              <AddIcon />
            </IconButton>
          )}
          <IconButton size="small" onClick={onClose}>
            <CloseIcon />
          </IconButton>
        </Box>
      </Box>
      <Divider />
      <List sx={{ p: 0 }}>
        {loading ? (
          <ListItem>
            <ListItemText primary="Loading chats..." />
          </ListItem>
        ) : (
        messages.map((message, index) => (
          <React.Fragment key={message.id}>
            <ListItem disablePadding>
              <ListItemButton onClick={() => onConversationClick(message)}>
                <ListItemAvatar>
                  <Avatar sx={{ bgcolor: message.avatarColor }}>
                    {message.sender.charAt(0)}
                  </Avatar>
                </ListItemAvatar>
                <ListItemText
                  primary={
                    <Typography variant="body2" sx={{ fontWeight: message.unread ? 'bold' : 'normal' }}>
                      {message.sender}
                    </Typography>
                  }
                  secondary={
                    <Typography variant="caption" color="text.secondary">
                      {message.preview}
                    </Typography>
                  }
                />
                <Typography variant="caption" color="text.secondary" sx={{ ml: 1 }}>
                  {message.time}
                </Typography>
              </ListItemButton>
            </ListItem>
            {index < messages.length - 1 && <Divider />}
          </React.Fragment>
        )))}
      </List>
    </Box>
  );
}