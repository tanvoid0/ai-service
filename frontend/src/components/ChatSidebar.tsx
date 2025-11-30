import { useState } from 'react';
import { FontAwesomeIcon } from '@fortawesome/react-fontawesome';
import {
  faPlus,
  faMessage,
  faFolder,
  faFolderOpen,
  faTrash,
  faEdit,
  faChevronDown,
  faChevronRight,
} from '@fortawesome/free-solid-svg-icons';
import { ChatStore } from '../utils/chatStore';
import type { Conversation } from '../types/chat';

interface ChatSidebarProps {
  conversations: Conversation[];
  currentConversationId: string | null;
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
  onRenameConversation: (id: string, newTitle: string) => void;
}

export default function ChatSidebar({
  conversations,
  currentConversationId,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  onRenameConversation,
}: ChatSidebarProps) {
  const [expandedFolders, setExpandedFolders] = useState<Set<string>>(new Set());
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editValue, setEditValue] = useState('');

  const folders = ChatStore.getFolders();
  const conversationsWithoutFolder = conversations.filter((c) => !c.folderId);

  const toggleFolder = (folderId: string) => {
    const newExpanded = new Set(expandedFolders);
    if (newExpanded.has(folderId)) {
      newExpanded.delete(folderId);
    } else {
      newExpanded.add(folderId);
    }
    setExpandedFolders(newExpanded);
  };

  const handleRename = (id: string, currentTitle: string) => {
    setEditingId(id);
    setEditValue(currentTitle);
  };

  const saveRename = (id: string) => {
    if (editValue.trim()) {
      onRenameConversation(id, editValue.trim());
    }
    setEditingId(null);
    setEditValue('');
  };

  return (
    <div className="w-64 bg-gray-900 text-white flex flex-col h-full">
      {/* New Chat Button */}
      <button
        onClick={onNewConversation}
        className="m-3 px-4 py-2 bg-primary-400 hover:bg-primary-500 rounded-lg flex items-center gap-2 transition-colors"
      >
        <FontAwesomeIcon icon={faPlus} />
        <span>New Chat</span>
      </button>

      {/* Scrollable Chat List */}
      <div className="flex-1 overflow-y-auto px-2">
        {/* Folders */}
        {folders.map((folder) => {
          const folderConversations = conversations.filter((c) => c.folderId === folder.id);
          const isExpanded = expandedFolders.has(folder.id);

          return (
            <div key={folder.id} className="mb-2">
              <button
                onClick={() => toggleFolder(folder.id)}
                className="w-full px-3 py-2 flex items-center gap-2 hover:bg-gray-800 rounded-lg transition-colors"
              >
                <FontAwesomeIcon
                  icon={isExpanded ? faChevronDown : faChevronRight}
                  className="w-3 h-3"
                />
                <FontAwesomeIcon
                  icon={isExpanded ? faFolderOpen : faFolder}
                  className="w-4 h-4"
                />
                <span className="flex-1 text-left truncate">{folder.name}</span>
                <span className="text-xs text-gray-400">{folderConversations.length}</span>
              </button>

              {isExpanded && (
                <div className="ml-6 mt-1 space-y-1">
                  {folderConversations.map((conv) => (
                    <ChatItem
                      key={conv.id}
                      conversation={conv}
                      isActive={conv.id === currentConversationId}
                      onSelect={() => onSelectConversation(conv.id)}
                      onDelete={() => onDeleteConversation(conv.id)}
                      onRename={() => handleRename(conv.id, conv.title)}
                      editingId={editingId}
                      editValue={editValue}
                      onEditChange={setEditValue}
                      onSaveEdit={() => saveRename(conv.id)}
                      onCancelEdit={() => setEditingId(null)}
                    />
                  ))}
                </div>
              )}
            </div>
          );
        })}

        {/* Conversations without folder */}
        <div className="space-y-1">
          {conversationsWithoutFolder.map((conv) => (
            <ChatItem
              key={conv.id}
              conversation={conv}
              isActive={conv.id === currentConversationId}
              onSelect={() => onSelectConversation(conv.id)}
              onDelete={() => onDeleteConversation(conv.id)}
              onRename={() => handleRename(conv.id, conv.title)}
              editingId={editingId}
              editValue={editValue}
              onEditChange={setEditValue}
              onSaveEdit={() => saveRename(conv.id)}
              onCancelEdit={() => setEditingId(null)}
            />
          ))}
        </div>
      </div>
    </div>
  );
}

interface ChatItemProps {
  conversation: Conversation;
  isActive: boolean;
  onSelect: () => void;
  onDelete: () => void;
  onRename: () => void;
  editingId: string | null;
  editValue: string;
  onEditChange: (value: string) => void;
  onSaveEdit: () => void;
  onCancelEdit: () => void;
}

function ChatItem({
  conversation,
  isActive,
  onSelect,
  onDelete,
  onRename,
  editingId,
  editValue,
  onEditChange,
  onSaveEdit,
  onCancelEdit,
}: ChatItemProps) {
  const isEditing = editingId === conversation.id;

  return (
    <div
      className={`group relative px-3 py-2 rounded-lg cursor-pointer transition-colors ${
        isActive ? 'bg-gray-800' : 'hover:bg-gray-800'
      }`}
      onClick={!isEditing ? onSelect : undefined}
    >
      {isEditing ? (
        <input
          type="text"
          value={editValue}
          onChange={(e) => onEditChange(e.target.value)}
          onBlur={onSaveEdit}
          onKeyDown={(e) => {
            if (e.key === 'Enter') onSaveEdit();
            if (e.key === 'Escape') onCancelEdit();
          }}
          className="w-full bg-gray-700 text-white px-2 py-1 rounded text-sm"
          autoFocus
          onClick={(e) => e.stopPropagation()}
        />
      ) : (
        <>
          <div className="flex items-center gap-2">
            <FontAwesomeIcon icon={faMessage} className="w-4 h-4 text-gray-400" />
            <span className="flex-1 truncate text-sm">{conversation.title}</span>
          </div>
          <div className="absolute right-2 top-1/2 -translate-y-1/2 opacity-0 group-hover:opacity-100 flex gap-1 transition-opacity">
            <button
              onClick={(e) => {
                e.stopPropagation();
                onRename();
              }}
              className="p-1 hover:bg-gray-700 rounded"
              title="Rename"
            >
              <FontAwesomeIcon icon={faEdit} className="w-3 h-3" />
            </button>
            <button
              onClick={(e) => {
                e.stopPropagation();
                onDelete();
              }}
              className="p-1 hover:bg-red-600 rounded"
              title="Delete"
            >
              <FontAwesomeIcon icon={faTrash} className="w-3 h-3" />
            </button>
          </div>
        </>
      )}
    </div>
  );
}

