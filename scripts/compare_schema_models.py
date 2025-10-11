#!/usr/bin/env python3
"""
Script to compare database schema.sql with SQLAlchemy models
Ensures both are perfectly synchronized
"""

import os
import sys
import re
from typing import Dict, List, Set

# Add app to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

class SchemaModelComparer:
    def __init__(self):
        self.schema_file = os.path.join(os.path.dirname(__file__), '..', 'schema.sql')
        self.models_file = os.path.join(os.path.dirname(__file__), '..', 'app', 'infrastructure', 'database', 'models.py')
        self.errors = []
        self.warnings = []
        
    def parse_schema_sql(self) -> Dict[str, Dict[str, str]]:
        """Parse schema.sql to extract table definitions"""
        with open(self.schema_file, 'r') as f:
            content = f.read()
        
        tables = {}
        
        # Find CREATE TABLE statements
        table_pattern = r'CREATE TABLE (\w+) \((.*?)\);'
        matches = re.findall(table_pattern, content, re.DOTALL | re.IGNORECASE)
        
        for table_name, table_def in matches:
            columns = {}
            
            # Parse column definitions
            lines = table_def.split('\n')
            for line in lines:
                line = line.strip()
                if line and not line.startswith('--') and not line.startswith('PRIMARY KEY') and not line.startswith('FOREIGN KEY'):
                    # Extract column info
                    if line.startswith('CONSTRAINT') or line.startswith('CHECK'):
                        continue
                        
                    # Clean up line
                    line = re.sub(r',\s*$', '', line)  # Remove trailing comma
                    
                    # Parse column definition
                    col_match = re.match(r'(\w+)\s+([A-Z]+(?:\([^)]+\))?)', line)
                    if col_match:
                        col_name, col_type = col_match.groups()
                        
                        # Handle common type variations
                        col_type = col_type.upper()
                        if 'TIMESTAMPTZ' in col_type:
                            col_type = 'TIMESTAMPTZ'
                        elif 'TIMESTAMP' in col_type:
                            col_type = 'TIMESTAMP'
                        elif 'NUMERIC' in col_type:
                            col_type = 'NUMERIC'
                        elif col_type == 'UUID':
                            col_type = 'UUID'
                        elif col_type == 'TEXT':
                            col_type = 'TEXT'
                        elif col_type in ['INT', 'INTEGER']:
                            col_type = 'INTEGER'
                        elif col_type == 'BOOLEAN':
                            col_type = 'BOOLEAN'
                        elif 'JSONB' in col_type:
                            col_type = 'JSONB'
                        elif 'JSON' in col_type:
                            col_type = 'JSON'
                        
                        # Check for constraints
                        nullable = 'NOT NULL' not in line
                        unique = 'UNIQUE' in line
                        
                        columns[col_name] = {
                            'type': col_type,
                            'nullable': nullable,
                            'unique': unique
                        }
            
            tables[table_name] = columns
            
        return tables
    
    def parse_models_py(self) -> Dict[str, Dict[str, str]]:
        """Parse models.py to extract SQLAlchemy model definitions"""
        with open(self.models_file, 'r') as f:
            content = f.read()
        
        tables = {}
        
        # Find class definitions
        class_pattern = r'class (\w+Model)\(Base\):(.*?)(?=class \w+Model\(Base\):|$)'
        matches = re.findall(class_pattern, content, re.DOTALL)
        
        for class_name, class_def in matches:
            # Extract table name
            table_match = re.search(r'__tablename__\s*=\s*["\'](\w+)["\']', class_def)
            if not table_match:
                continue
                
            table_name = table_match.group(1)
            columns = {}
            
            # Find column definitions
            col_pattern = r'(\w+)\s*=\s*Column\((.*?)\)'
            col_matches = re.findall(col_pattern, class_def, re.DOTALL)
            
            for col_name, col_def in col_matches:
                # Parse column type and constraints
                col_type = None
                nullable = True
                unique = False
                
                # Extract type
                if 'PostgreSQL_UUID' in col_def:
                    col_type = 'UUID'
                elif 'Numeric' in col_def:
                    col_type = 'NUMERIC'
                elif 'DateTime' in col_def and 'timezone=True' in col_def:
                    col_type = 'TIMESTAMPTZ'
                elif 'DateTime' in col_def:
                    col_type = 'TIMESTAMP'
                elif 'Text' in col_def:
                    col_type = 'TEXT'
                elif 'Integer' in col_def:
                    col_type = 'INTEGER'
                elif 'Boolean' in col_def:
                    col_type = 'BOOLEAN'
                elif 'JSON' in col_def:
                    col_type = 'JSON'
                
                # Check constraints
                if 'nullable=False' in col_def:
                    nullable = False
                if 'unique=True' in col_def:
                    unique = True
                
                if col_type:
                    columns[col_name] = {
                        'type': col_type,
                        'nullable': nullable,
                        'unique': unique
                    }
            
            tables[table_name] = columns
        
        return tables
    
    def compare_tables(self):
        """Compare schema and models"""
        print("Parsing schema.sql...")
        schema_tables = self.parse_schema_sql()
        
        print("Parsing models.py...")
        model_tables = self.parse_models_py()
        
        print(f"\nFound {len(schema_tables)} tables in schema.sql")
        print(f"Found {len(model_tables)} tables in models.py")
        
        # Compare table presence
        schema_table_names = set(schema_tables.keys())
        model_table_names = set(model_tables.keys())
        
        missing_in_models = schema_table_names - model_table_names
        missing_in_schema = model_table_names - schema_table_names
        
        if missing_in_models:
            self.errors.append(f"Tables in schema but missing in models: {missing_in_models}")
        
        if missing_in_schema:
            self.warnings.append(f"Tables in models but missing in schema: {missing_in_schema}")
        
        # Compare common tables
        common_tables = schema_table_names & model_table_names
        
        for table_name in common_tables:
            self.compare_table_columns(table_name, schema_tables[table_name], model_tables[table_name])
    
    def compare_table_columns(self, table_name: str, schema_cols: Dict, model_cols: Dict):
        """Compare columns between schema and model for a specific table"""
        schema_col_names = set(schema_cols.keys())
        model_col_names = set(model_cols.keys())
        
        missing_in_model = schema_col_names - model_col_names
        missing_in_schema = model_col_names - schema_col_names
        
        if missing_in_model:
            self.errors.append(f"Table {table_name}: Columns in schema but missing in model: {missing_in_model}")
        
        if missing_in_schema:
            self.warnings.append(f"Table {table_name}: Columns in model but missing in schema: {missing_in_schema}")
        
        # Compare common columns
        common_cols = schema_col_names & model_col_names
        
        for col_name in common_cols:
            schema_col = schema_cols[col_name]
            model_col = model_cols[col_name]
            
            # Compare types
            if schema_col['type'] != model_col['type']:
                self.errors.append(
                    f"Table {table_name}, column {col_name}: "
                    f"Type mismatch - schema: {schema_col['type']}, model: {model_col['type']}"
                )
            
            # Compare nullable
            if schema_col['nullable'] != model_col['nullable']:
                self.warnings.append(
                    f"Table {table_name}, column {col_name}: "
                    f"Nullable mismatch - schema: {schema_col['nullable']}, model: {model_col['nullable']}"
                )
            
            # Compare unique constraints
            if schema_col['unique'] != model_col['unique']:
                self.errors.append(
                    f"Table {table_name}, column {col_name}: "
                    f"Unique constraint mismatch - schema: {schema_col['unique']}, model: {model_col['unique']}"
                )
    
    def validate_specific_constraints(self):
        """Validate specific constraints we know should exist"""
        print("\nValidating critical constraints...")
        
        # Check for donation table specifics
        with open(self.schema_file, 'r') as f:
            schema_content = f.read()
        
        # Check unique constraints
        donation_section = re.search(r'CREATE TABLE donation.*?;', schema_content, re.DOTALL)
        if donation_section:
            donation_text = donation_section.group(0)
            
            # Check for reference_code UNIQUE
            if 'reference_code TEXT NOT NULL UNIQUE' not in donation_text:
                self.errors.append("reference_code should be TEXT NOT NULL UNIQUE in donation table")
            
            # Check for correlation_id UNIQUE
            if 'correlation_id TEXT NOT NULL UNIQUE' not in donation_text:
                self.errors.append("correlation_id should be TEXT NOT NULL UNIQUE in donation table")
            
            # Check for amount constraint
            if 'CHECK (amount_gtq > 0)' not in donation_text:
                self.errors.append("amount_gtq should have CHECK constraint (amount_gtq > 0)")
        
        # Check models for same constraints
        with open(self.models_file, 'r') as f:
            models_content = f.read()
        
        donation_model_match = re.search(r'class DonationModel.*?def __repr__', models_content, re.DOTALL)
        if donation_model_match:
            donation_model_text = donation_model_match.group(0)
            
            # Check for reference_code unique
            if 'reference_code = Column(Text, nullable=False, unique=True' not in donation_model_text:
                self.errors.append("DonationModel.reference_code should be Text, nullable=False, unique=True")
            
            # Check for correlation_id unique  
            if 'correlation_id = Column(Text, nullable=False, unique=True' not in donation_model_text:
                self.errors.append("DonationModel.correlation_id should be Text, nullable=False, unique=True")
    
    def run_comparison(self):
        """Run complete comparison"""
        print("="*60)
        print("SCHEMA vs MODELS COMPARISON")
        print("="*60)
        
        try:
            self.compare_tables()
            self.validate_specific_constraints()
            
            # Report results
            print("\n" + "="*60)
            print("COMPARISON RESULTS")
            print("="*60)
            
            if not self.errors and not self.warnings:
                print("✅ PERFECT MATCH!")
                print("Schema and models are perfectly synchronized!")
            else:
                if self.errors:
                    print(f"❌ CRITICAL ERRORS ({len(self.errors)}):")
                    for i, error in enumerate(self.errors, 1):
                        print(f"  {i}. {error}")
                
                if self.warnings:
                    print(f"\n⚠️  WARNINGS ({len(self.warnings)}):")
                    for i, warning in enumerate(self.warnings, 1):
                        print(f"  {i}. {warning}")
            
            print("\n" + "="*60)
            
            return len(self.errors) == 0
            
        except Exception as e:
            print(f"❌ Error during comparison: {e}")
            return False

def main():
    """Main comparison function"""
    comparer = SchemaModelComparer()
    success = comparer.run_comparison()
    
    if success:
        print("\n🎉 Schema and models are properly synchronized!")
        sys.exit(0)
    else:
        print("\n💥 Schema and models are out of sync. Please fix the errors above.")
        sys.exit(1)

if __name__ == "__main__":
    main()
