import React from 'react';
import { Routes, Route } from 'react-router-dom';
import RulesList from './RulesList.tsx';
import RuleForm from './RuleForm.tsx';
import KeywordsPage from './Keywords.tsx';
import ReplacementsPage from './Replacements.tsx';

const RulesPage: React.FC = () => {
  return (
    <Routes>
      <Route index element={<RulesList />} />
      <Route path="new" element={<RuleForm />} />
      <Route path=":id/edit" element={<RuleForm />} />
      <Route path=":id/keywords" element={<KeywordsPage />} />
      <Route path=":id/replacements" element={<ReplacementsPage />} />
    </Routes>
  );
};

export default RulesPage;
