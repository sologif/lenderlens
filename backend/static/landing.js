document.addEventListener('DOMContentLoaded',()=>{
  const scenarios={
    fraudulent:{brand:'FastCash Instant Loans',domain:'fastcash-instantloans.net',tag:'Quick approval · minimal documents · ₹1,500 security deposit',fee:'₹1,500 upfront',score:91,decision:'BLOCK',tone:'danger',reasons:[['×','Identity mismatch','Domain is not registered to the claimed lender.','CRITICAL'],['×','Advance fee detected','₹1,500 requested before loan disbursal.','CRITICAL'],['!','Invasive permissions','Contacts, SMS, call logs and photos requested.','HIGH'],['×','Fraud network link','3 flagged domains + 2 suspicious payment endpoints.','HIGH']]},
    uncertain:{brand:'QuickLoan',domain:'quickloan-app.in',tag:'Fast personal loans · partial disclosures · contact permission requested',fee:'Processing fee: disclose later',score:56,decision:'REVIEW',tone:'warning',reasons:[['!','Domain not verified','The lender identity exists, but this web domain is not registered as official.','HIGH'],['!','KFS incomplete','Key loan disclosures are present but incomplete.','MEDIUM'],['!','Permission request','Contacts access is requested during onboarding.','MEDIUM'],['✓','Registry entity found','Claimed lender has a matching registry record.','LOW']]},
    legitimate:{brand:'ABC Finance',domain:'abcfinance.com',tag:'Transparent personal loan · verified registration · ₹0 advance fee',fee:'₹0 advance fee',score:18,decision:'ALLOW',tone:'success',reasons:[['✓','Identity verified','Registered entity and official domain are consistent.','LOW'],['✓','Loan disclosures clear','KFS and APR disclosure are available before application.','LOW'],['✓','No invasive permissions','No unusual device permissions requested.','LOW'],['✓','Network isolated','No suspicious connected entities in the demo graph.','LOW']]}
  };
  const $=s=>document.querySelector(s);
  function render(name){
    const d=scenarios[name]; if(!d)return;
    document.querySelectorAll('.scenario').forEach(b=>b.classList.toggle('active',b.dataset.scenario===name));
    $('#demoBrand').textContent=d.brand; $('#demoDomain').textContent=d.domain; $('#demoTag').textContent=d.tag; $('#demoFee').textContent=d.fee;
    $('#demoUrl').value=d.domain+'/apply'; $('#demoScore').textContent=d.score; $('#demoDecision').textContent=d.decision; $('#demoDecision').className='risk-badge '+d.tone;
    $('#demoMeter').style.width=d.score+'%'; $('#demoMeter').style.background=d.tone==='danger'?'#d92d20':d.tone==='warning'?'#dc6803':'#039855';
    $('#scanState').innerHTML='ANALYSIS COMPLETE <span>•</span> <span>0.8s</span>';
    $('#reasonList').innerHTML=d.reasons.map(r=>`<div class="reason ${r[0]==='×'?'danger':r[0]==='!'?'warning':'success'}"><span class="icon">${r[0]}</span><p><b>${r[1]}</b><small>${r[2]}</small></p><span class="weight">${r[3]}</span></div>`).join('');
    const hero=$('#heroScore'); if(hero){hero.textContent=d.score;$('#heroMeter').style.width=d.score+'%';$('#heroMeter').style.background=d.tone==='danger'?'#f04438':d.tone==='warning'?'#f79009':'#12b76a';$('#heroStatus').textContent=d.score>70?'HIGH RISK':d.score>30?'REVIEW':'LOW RISK';$('#heroStatus').className='risk-badge '+d.tone;}
  }
  document.querySelectorAll('.scenario').forEach(b=>b.addEventListener('click',()=>render(b.dataset.scenario)));
  const scan=$('#demoScan'); if(scan)scan.addEventListener('click',()=>{const original=scan.textContent;scan.textContent='Scanning…';$('#scanState').textContent='ANALYZING PAGE…';setTimeout(()=>{scan.textContent=original;render(document.querySelector('.scenario.active').dataset.scenario)},650)});
  document.querySelectorAll('a[data-scroll]').forEach(a=>a.addEventListener('click',e=>{const el=$(a.dataset.scroll);if(el){e.preventDefault();el.scrollIntoView({behavior:'smooth'})}}));
  $('#showDashboard')?.addEventListener('click',()=>{window.location.href='/dashboard/index.html'});
  render('fraudulent');
});
