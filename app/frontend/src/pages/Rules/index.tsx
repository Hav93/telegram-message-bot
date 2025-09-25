import React from 'react';
import { Routes, Route } from 'react-router-dom';
import RulesList from './RulesList';
import RuleForm from './RuleForm';
import KeywordsPage from './Keywords';
import ReplacementsPage from './Replacements';

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
