// src/components/App.tsx

import ConversationView from './ConversationView';

function App() {
  return (
    <div className="min-h-screen bg-gray-50 py-8">
      <div className="container mx-auto">
        <ConversationView />
      </div>
    </div>
  );
}

export default App;
