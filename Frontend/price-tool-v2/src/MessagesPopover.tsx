import * as React from 'react';
import {
  Popover,
  Box,
  Typography,
  IconButton,
  List,
  ListItem,
  ListItemButton,
  ListItemAvatar,
  Avatar,
  ListItemText,
  Divider,
} from '@mui/material';
import ArrowBackIcon from '@mui/icons-material/ArrowBack';
import CloseIcon from '@mui/icons-material/Close';
import MessageList, { Message } from './MessageList';
import ChatThread, { ChatMessage } from './ChatThread';

const API_BASE = '';

interface MessagesPopoverProps {
  anchorEl: HTMLElement | null;
  onClose: () => void;
  loggedInUser: {
    id?: number;
    email: string;
    name?: string;
  } | null;
}

const AVATAR_COLORS = ['#1976d2', '#9c27b0', '#2196f3', '#4caf50', '#ff9800'];

function getAvatarColor(id: number): string {
  return AVATAR_COLORS[(id - 1) % AVATAR_COLORS.length];
}

function formatTime(isoStr: string): string {
  try {
    const d = new Date(isoStr);
    return d.toLocaleTimeString('en-US', { hour: 'numeric', minute: '2-digit' });
  } catch {
    return '';
  }
}

export default function MessagesPopover({ anchorEl, onClose, loggedInUser }: MessagesPopoverProps) {
  const [chats, setChats] = React.useState<Array<{ chat_id: number; type: string; name: string | null; created_at: string; participant_ids: number[] }>>([]);
  const [users, setUsers] = React.useState<Array<{ id: number; name: string; email: string }>>([]);
  const [messagesList, setMessagesList] = React.useState<Message[]>([]);
  const [selectedConversation, setSelectedConversation] = React.useState<Message | null>(null);
  const [chatMessages, setChatMessages] = React.useState<ChatMessage[]>([]);
  const [loading, setLoading] = React.useState(false);
  const [loadingMessages, setLoadingMessages] = React.useState(false);
  const [showNewChatPicker, setShowNewChatPicker] = React.useState(false);
  const [creatingChat, setCreatingChat] = React.useState(false);
  const [newChatError, setNewChatError] = React.useState<string | null>(null);
  const rawMessagesRef = React.useRef<Array<{ id: number; sender_id: number; body: string; created_at: string }>>([]);

  const currentUserId = loggedInUser?.id;
  const otherUsers = users.filter((u) => u.id !== currentUserId);
  const groupChat = React.useMemo(() => chats.find((c) => c.type === 'group'), [chats]);

  // Chats: GET /api/chats (header X-User-Id). Groups (e.g. "All") and direct chats.
  // Users: GET /api/users – used to show names in New chat and in message list.
  React.useEffect(() => {
    if (!anchorEl || !currentUserId) return;
    setLoading(true);
    fetch(`${API_BASE}/api/chats`, {
      headers: { 'X-User-Id': String(currentUserId) },
    })
      .then((res) => res.json())
      .then((data) => {
        setChats(data.chats || []);
      })
      .catch(() => setChats([]))
      .finally(() => setLoading(false));

    fetch(`${API_BASE}/api/users`)
      .then((res) => res.json())
      .then((data) => {
        setUsers(data.users || []);
      })
      .catch(() => setUsers([]));
  }, [anchorEl, currentUserId]);

  React.useEffect(() => {
    const sorted = [...chats].sort((a, b) => (a.type === 'group' ? -1 : b.type === 'group' ? 1 : 0));
    const list: Message[] = sorted.map((c) => {
      const otherId = c.participant_ids?.find((id) => id !== currentUserId);
      const other = users.find((u) => u.id === otherId);
      const displayName = c.type === 'group' ? (c.name || 'All') : (other?.name || other?.email || `User ${otherId ?? c.chat_id}`);
      return {
        id: c.chat_id,
        sender: displayName,
        preview: c.type === 'group' ? 'Group chat' : 'Chat',
        time: formatTime(c.created_at),
        avatarColor: getAvatarColor(c.chat_id),
      };
    });
    setMessagesList(list);
  }, [chats, users, currentUserId]);

  const mapRawToChatMessages = React.useCallback(
    (raw: Array<{ id: number; sender_id: number; body: string; created_at: string }>) =>
      raw.map((m) => {
        const sender = users.find((u) => u.id === m.sender_id);
        const senderName = sender ? (sender.name || sender.email) : `User ${m.sender_id}`;
        return {
          id: m.id,
          sender: senderName,
          message: m.body,
          time: formatTime(m.created_at),
          isCurrentUser: m.sender_id === currentUserId,
        };
      }),
    [users, currentUserId]
  );

  React.useEffect(() => {
    if (rawMessagesRef.current.length === 0) return;
    setChatMessages(mapRawToChatMessages(rawMessagesRef.current));
  }, [users, mapRawToChatMessages]);

  const handleConversationClick = (message: Message) => {
    setSelectedConversation(message);
    setChatMessages([]);
    if (!currentUserId) return;
    setLoadingMessages(true);
    fetch(`${API_BASE}/api/chats/${message.id}/messages`, {
      headers: { 'X-User-Id': String(currentUserId) },
    })
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load messages');
        return res.json();
      })
      .then((data) => {
        const raw = data.messages || [];
        rawMessagesRef.current = raw;
        setChatMessages(mapRawToChatMessages(raw));
      })
      .catch(() => {
        rawMessagesRef.current = [];
        setChatMessages([]);
      })
      .finally(() => setLoadingMessages(false));
  };

  const handleBack = () => {
    setSelectedConversation(null);
    setChatMessages([]);
    rawMessagesRef.current = [];
  };

  const handleNewChat = () => {
    setShowNewChatPicker(true);
    setNewChatError(null);
  };

  const openChatAndLoadMessages = (message: Message) => {
    setSelectedConversation(message);
    setShowNewChatPicker(false);
    setNewChatError(null);
    setChatMessages([]);
    if (!currentUserId) return;
    setLoadingMessages(true);
    fetch(`${API_BASE}/api/chats/${message.id}/messages`, {
      headers: { 'X-User-Id': String(currentUserId) },
    })
      .then((res) => {
        if (!res.ok) throw new Error('Failed to load messages');
        return res.json();
      })
      .then((data) => {
        const raw = data.messages || [];
        rawMessagesRef.current = raw;
        setChatMessages(mapRawToChatMessages(raw));
      })
      .catch(() => {
        rawMessagesRef.current = [];
        setChatMessages([]);
      })
      .finally(() => setLoadingMessages(false));
  };

  const handleStartDirectChat = (otherUserId: number) => {
    if (!currentUserId) return;
    setNewChatError(null);
    setCreatingChat(true);
    fetch(`${API_BASE}/api/chats/direct`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': String(currentUserId),
      },
      body: JSON.stringify({ user_id: otherUserId }),
    })
      .then(async (res) => {
        const body = await res.json().catch(() => ({}));
        if (!res.ok) {
          throw new Error((body.detail as string) || body.message || 'Failed to start chat');
        }
        return body as { chat_id: number; type: string; participant_ids: number[] };
      })
      .then((data) => {
        const newChat = {
          chat_id: data.chat_id,
          type: data.type,
          name: null as string | null,
          created_at: new Date().toISOString(),
          participant_ids: data.participant_ids || [currentUserId, otherUserId],
        };
        setChats((prev) => {
          if (prev.some((c) => c.chat_id === data.chat_id)) return prev;
          return [...prev, newChat];
        });
        const other = users.find((u) => u.id === otherUserId);
        const displayName = other?.name || other?.email || `User ${otherUserId}`;
        const newMessage: Message = {
          id: data.chat_id,
          sender: displayName,
          preview: 'Chat',
          time: formatTime(newChat.created_at),
          avatarColor: getAvatarColor(data.chat_id),
        };
        setSelectedConversation(newMessage);
        setShowNewChatPicker(false);
        setChatMessages([]);
        setLoadingMessages(true);
        fetch(`${API_BASE}/api/chats/${data.chat_id}/messages`, {
          headers: { 'X-User-Id': String(currentUserId) },
        })
          .then((r) => r.json())
          .then((payload) => {
            const raw = payload.messages || [];
            rawMessagesRef.current = raw;
            setChatMessages(mapRawToChatMessages(raw));
          })
          .catch(() => {
            rawMessagesRef.current = [];
          })
          .finally(() => setLoadingMessages(false));
      })
      .catch((err: Error) => {
        setNewChatError(err.message || 'Could not start chat. Is the backend running?');
      })
      .finally(() => setCreatingChat(false));
  };

  const handleSendMessage = (messageText: string) => {
    if (!selectedConversation || !currentUserId) return;
    fetch(`${API_BASE}/api/chats/${selectedConversation.id}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-User-Id': String(currentUserId),
      },
      body: JSON.stringify({ body: messageText }),
    })
      .then((res) => {
        if (!res.ok) throw new Error('Failed to send');
        return res.json();
      })
      .then((data) => {
        const me = users.find((u) => u.id === currentUserId);
        const senderName = me ? (me.name || me.email) : 'You';
        const newMsg: ChatMessage = {
          id: data.id,
          sender: senderName,
          message: data.body,
          time: formatTime(new Date().toISOString()),
          isCurrentUser: true,
        };
        setChatMessages((prev) => [...prev, newMsg]);
      })
      .catch(() => {});
  };

  const open = Boolean(anchorEl);
  const id = open ? 'messages-popover' : undefined;

  return (
    <Popover
      id={id}
      open={open}
      anchorEl={anchorEl}
      onClose={() => {
        onClose();
        setShowNewChatPicker(false);
      }}
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
          width: 400,
          maxHeight: 600,
          mt: 1,
        },
      }}
    >
      {showNewChatPicker ? (
        <Box>
          <Box sx={{ p: 2, display: 'flex', alignItems: 'center', gap: 1 }}>
            <IconButton size="small" onClick={() => setShowNewChatPicker(false)} aria-label="Back">
              <ArrowBackIcon />
            </IconButton>
            <Typography variant="h6" sx={{ fontWeight: 'bold', flexGrow: 1 }}>
              New chat
            </Typography>
            <IconButton size="small" onClick={onClose}>
              <CloseIcon />
            </IconButton>
          </Box>
          <Divider />
          {newChatError && (
            <Box sx={{ px: 2, py: 1, bgcolor: 'error.light', color: 'error.contrastText', typography: 'body2' }}>
              {newChatError}
            </Box>
          )}
          <List sx={{ p: 0 }}>
            {creatingChat ? (
              <ListItem>
                <ListItemText primary="Creating chat..." />
              </ListItem>
            ) : (
              <>
                {groupChat ? (() => {
                  const groupMessage: Message = {
                    id: groupChat.chat_id,
                    sender: groupChat.name || 'All',
                    preview: 'Group chat',
                    time: formatTime(groupChat.created_at),
                    avatarColor: getAvatarColor(groupChat.chat_id),
                  };
                  return (
                    <React.Fragment key="group-section">
                      <ListItem sx={{ pt: 1, pb: 0 }}>
                        <ListItemText primary="Group" secondary="Chat with everyone" sx={{ "& .MuiListItemText-primary": { fontSize: '0.75rem', fontWeight: 600, color: 'text.secondary', textTransform: 'uppercase' } }} />
                      </ListItem>
                      <ListItem key={`group-${groupChat.chat_id}`} disablePadding>
                        <ListItemButton onClick={() => openChatAndLoadMessages(groupMessage)}>
                          <ListItemAvatar>
                            <Avatar sx={{ bgcolor: getAvatarColor(groupChat.chat_id) }}>A</Avatar>
                          </ListItemAvatar>
                          <ListItemText primary="All" secondary="Everyone in the app" />
                        </ListItemButton>
                      </ListItem>
                      <ListItem sx={{ pt: 1, pb: 0 }}>
                        <ListItemText primary="Direct message" sx={{ "& .MuiListItemText-primary": { fontSize: '0.75rem', fontWeight: 600, color: 'text.secondary', textTransform: 'uppercase' } }} />
                      </ListItem>
                    </React.Fragment>
                  );
                })() : (
                  <ListItem>
                    <ListItemText primary="No group yet. Restart backend to create 'All' group." secondary="Then refresh Messages." />
                  </ListItem>
                )}
                {otherUsers.map((user) => (
                  <ListItem key={user.id} disablePadding>
                    <ListItemButton onClick={() => handleStartDirectChat(user.id)}>
                      <ListItemAvatar>
                        <Avatar sx={{ bgcolor: getAvatarColor(user.id) }}>{user.name?.charAt(0) || user.email?.charAt(0) || '?'}</Avatar>
                      </ListItemAvatar>
                      <ListItemText
                        primary={user.name || user.email}
                        secondary={user.name ? user.email : undefined}
                      />
                    </ListItemButton>
                  </ListItem>
                ))}
              </>
            )}
          </List>
        </Box>
      ) : !selectedConversation ? (
        <MessageList
          messages={messagesList}
          onConversationClick={handleConversationClick}
          onClose={onClose}
          loading={loading}
          onNewChat={handleNewChat}
        />
      ) : (
        <ChatThread
          conversation={selectedConversation}
          messages={chatMessages}
          onBack={handleBack}
          onClose={onClose}
          onSendMessage={handleSendMessage}
          loadingMessages={loadingMessages}
        />
      )}
    </Popover>
  );
}