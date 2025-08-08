from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer
import os

def create_test_bill():
    filename = "test_bill.pdf"
    doc = SimpleDocTemplate(filename, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []
    
    # Title
    title = Paragraph("Test Government Bill: Climate Action Act 2024", styles['Title'])
    story.append(title)
    story.append(Spacer(1, 20))
    
    # Sections with substantial content for chunking
    sections = [
        {
            "title": "Section 1: Definitions and Purpose",
            "content": """This Act establishes comprehensive climate action policies to reduce greenhouse gas emissions by 50% by 2030. The purpose of this legislation is to create a framework for sustainable energy transition, carbon pricing mechanisms, and environmental protection measures. Key definitions include: (a) Carbon equivalent means the metric measure used to compare the warming potential of different greenhouse gases, (b) Renewable energy sources include solar, wind, hydroelectric, geothermal, and biomass energy systems, (c) Net zero emissions refers to achieving a balance between greenhouse gas emissions produced and those removed from the atmosphere."""
        },
        {
            "title": "Section 2: Carbon Pricing and Tax Provisions", 
            "content": """A carbon tax of $25 per ton of CO2 equivalent shall be implemented beginning January 1, 2025, increasing by $5 annually until reaching $50 per ton by 2030. Revenue generated from carbon pricing shall be distributed as follows: 40% for renewable energy infrastructure investments, 30% for direct rebates to low-income households, 20% for industrial decarbonization programs, and 10% for administrative costs. Companies with annual emissions exceeding 25,000 tons must register with the Environmental Protection Agency and submit quarterly emissions reports."""
        },
        {
            "title": "Section 3: Renewable Energy Mandates",
            "content": """Electric utilities must source 50% of electricity from renewable sources by 2028 and 100% by 2035. Utilities failing to meet renewable energy standards face penalties of $0.02 per kWh shortfall. The Department of Energy shall establish a renewable energy credit trading system allowing utilities to purchase credits from other providers. Priority consideration for federal grants shall be given to rural communities developing wind and solar projects. Energy storage requirements mandate utilities maintain storage capacity equivalent to 20% of peak demand by 2032."""
        },
        {
            "title": "Section 4: Transportation and Infrastructure",
            "content": """New vehicle emission standards require 50% of new vehicle sales to be electric by 2030. Federal agencies must transition their vehicle fleets to electric or hybrid vehicles by 2028, with annual progress reports submitted to Congress. Investment of $50 billion over 10 years shall support electric vehicle charging infrastructure, prioritizing underserved communities. Public transit systems receiving federal funding must develop electrification plans by 2026. Airlines and shipping companies must reduce emissions by 30% by 2030 through efficiency improvements and alternative fuel adoption."""
        },
        {
            "title": "Section 5: Industrial Regulations and Incentives",
            "content": """Manufacturing facilities must conduct energy audits every three years and implement cost-effective efficiency measures. Tax credits of up to 30% are available for investments in clean technology, carbon capture systems, and industrial heat pumps. Steel, cement, and chemical plants must develop decarbonization roadmaps by 2025 with binding emission reduction targets. Small businesses with fewer than 100 employees may access grants up to $100,000 for energy efficiency upgrades. Research and development tax credits for clean technology innovation are increased to 25% of qualifying expenses."""
        },
        {
            "title": "Section 6: Environmental Justice and Community Benefits",
            "content": """Disadvantaged communities shall receive priority for clean energy investments and environmental remediation funding. The Environmental Justice Advisory Council shall review all major climate policies for community impact. At least 40% of climate investment benefits must flow to disadvantaged communities facing cumulative environmental burdens. Community-based organizations may receive technical assistance grants to participate in environmental planning processes. Environmental health monitoring programs shall be established in communities with disproportionate pollution exposure, with annual public reporting requirements."""
        },
        {
            "title": "Section 7: Implementation Timeline and Enforcement",
            "content": """The Environmental Protection Agency shall issue implementing regulations within 180 days of enactment. States must submit compliance plans within one year demonstrating how they will achieve emission reduction targets. Non-compliance penalties range from $10,000 to $1,000,000 depending on violation severity and repeat offenses. The Act includes a citizen suit provision allowing individuals to enforce compliance through federal courts. Annual progress reports shall be submitted to Congress detailing emission reductions, economic impacts, and program effectiveness. This Act shall take effect immediately upon enactment, with staged implementation of specific provisions as outlined in each section."""
        }
    ]
    
    for section in sections:
        # Section header
        header = Paragraph(section["title"], styles['Heading1'])
        story.append(header)
        story.append(Spacer(1, 12))
        
        # Section content
        content = Paragraph(section["content"], styles['Normal'])
        story.append(content)
        story.append(Spacer(1, 20))
    
    # Build PDF
    doc.build(story)
    print(f"Created test PDF: {filename}")
    return filename

if __name__ == "__main__":
    create_test_bill()