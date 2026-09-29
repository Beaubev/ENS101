(function exposeNoteUtils(root, factory) {
  const api = factory();
  if (typeof module !== 'undefined' && module.exports) module.exports = api;
  if (root) root.NoteUtils = api;
})(typeof window !== 'undefined' ? window : globalThis, () => {
  const CONVERSATION_NOTE_TAG = '#SSTEAM';

  function ensurePermanentConversationTag(value = '') {
    const body = String(value ?? '')
      .replace(/\r\n/g, '\n')
      .split('\n')
      .filter(line => line.trim() !== CONVERSATION_NOTE_TAG)
      .join('\n')
      .replace(/^\n+|\n+$/g, '');

    return body ? `${CONVERSATION_NOTE_TAG}\n${body}` : CONVERSATION_NOTE_TAG;
  }

  return { CONVERSATION_NOTE_TAG, ensurePermanentConversationTag };
});
