import React, { useState } from 'react';
import {
  Box,
  Typography,
  IconButton,
  Divider,
  Avatar,
  TextField,
  Paper,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CloseIcon from '@mui/icons-material/Close';
import SendIcon from '@mui/icons-material/Send';

export interface ChatMessage {
  id: number;
  sender: string;
  message: string;
  time: string;
  isCurrentUser: boolean;
}

interface Message {
  id: number;
  sender: string;
  preview: string;
  time: string;
  avatarColor: string;
  active?: boolean;
  unread?: boolean;
}

interface ChatThreadProps {
  conversation: Message;
  messages: ChatMessage[];
  onBack: () => void;
  onClose: () => void;
  onSendMessage: (message: string) => void;
  loadingMessages?: boolean;
}

export default function ChatThread({ conversation, messages, onBack, onClose, onSendMessage, loadingMessages }: ChatThreadProps) {
  const [inputMessage, setInputMessage] = useState('');

  const handleSend = () => {
    if (inputMessage.trim()) {
      onSendMessage(inputMessage);
      setInputMessage('');
    }
  };

  const handleKeyPress = (e: React.KeyboardEvent) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSend();
    }
  };

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', height: '100%' }}>
      {/* Header */}
      <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
        <IconButton size="small" onClick={onBack}>
          <ArrowBackIcon />
        </IconButton>
        <Avatar sx={{ bgcolor: conversation.avatarColor, width: 32, height: 32 }}>
          {conversation.sender.charAt(0)}
        </Avatar>
        <Typography variant="subtitle1" sx={{ flexGrow: 1, fontWeight: 'bold' }}>
          {conversation.sender}
        </Typography>
        <IconButton size="small" onClick={onClose}>
          <CloseIcon />
        </IconButton>
      </Box>
      <Divider />

      {/* Messages */}
      <Box sx={{ flexGrow: 1, p: 2, overflowY: 'auto', maxHeight: 400 }}>
        {loadingMessages ? (
          <Typography variant="body2" color="text.secondary">Loading messages...</Typography>
        ) : (
        messages.map((msg) => (
          <Box
            key={msg.id}
            sx={{
              display: 'flex',
              flexDirection: 'column',
              alignItems: msg.isCurrentUser ? 'flex-end' : 'flex-start',
              mb: 2,
            }}
          >
            <Typography variant="caption" sx={{ mb: 0.25, px: 0.5, color: 'text.secondary' }}>
              {msg.isCurrentUser ? 'You' : msg.sender}
            </Typography>
            <Paper
              sx={{
                p: 1.5,
                maxWidth: '70%',
                bgcolor: msg.isCurrentUser ? 'primary.main' : 'grey.200',
                color: msg.isCurrentUser ? 'white' : 'black',
              }}
            >
              <Typography variant="body2">{msg.message}</Typography>
              <Typography variant="caption" sx={{ display: 'block', mt: 0.5, opacity: 0.8 }}>
                {msg.time}
              </Typography>
            </Paper>
          </Box>
        )))}
      </Box>

      <Divider />

      {/* Input */}
      <Box sx={{ p: 2, display: 'flex', gap: 1 }}>
        <TextField
          fullWidth
          size="small"
          placeholder="Type a message..."
          value={inputMessage}
          onChange={(e) => setInputMessage(e.target.value)}
          onKeyPress={handleKeyPress}
        />
        <IconButton color="primary" onClick={handleSend} disabled={!inputMessage.trim()}>
          <SendIcon />
        </IconButton>
      </Box>
    </Box>
  );
}