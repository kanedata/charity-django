UPDATE_COMPANIES = {}

UPDATE_COMPANIES[
    "Update Accounts table"
] = """
INSERT INTO companies_account ("CompanyNumber", "financial_year_end", "category")
select "CompanyNumber",
	"Accounts_LastMadeUpDate" as financial_year_end,
	"Accounts_AccountCategory" as "category"
from companies_company 
where "Accounts_LastMadeUpDate" is not null
ON CONFLICT ("CompanyNumber", "financial_year_end")
DO
UPDATE SET category=EXCLUDED.category;
"""
