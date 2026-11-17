let selectedSpeech = null;
let chartInstances = {};
const $ = id => document.getElementById(id);
const api = async (url, options={}) => {
  const response = await fetch(url, {headers:{"Content-Type":"application/json"}, ...options});
  const data = await response.json();
  if (!response.ok) throw new Error(data.error || JSON.stringify(data));
  return data;
};
function drawChart(id, type, labels, values, label) {
  if (chartInstances[id]) chartInstances[id].destroy();
  chartInstances[id] = new Chart($(id), {
    type, data:{labels,datasets:[{label,data:values,backgroundColor:[
      "#426bd5","#19a18f","#e3a33d","#9272cf","#e47777","#56a5c8",
      "#7b9a62","#bf83a8","#8795a8","#d17c45"
    ],borderRadius:5,borderWidth:1}]},
    options:{responsive:true,maintainAspectRatio:false,plugins:{legend:{display:type==="doughnut"}} ,
      scales:type==="doughnut"?{}:{y:{beginAtZero:true,ticks:{precision:0}}}}
  });
}
function fmtTime(seconds){const s=Math.max(0,Math.floor(seconds||0));return `${String(Math.floor(s/60)).padStart(2,"0")}:${String(s%60).padStart(2,"0")}`;}
async function loadPoliticians(){
  const people=await api("/api/politicians/");
  $("politicianSelect").innerHTML='<option value="">Select politician</option>'+people.map(p=>`<option value="${p.id}">${escapeHtml(p.name)}${p.party?' · '+escapeHtml(p.party):''}</option>`).join("");
}
function escapeHtml(s){return String(s??"").replace(/[&<>"']/g,c=>({"&":"&amp;","<":"&lt;",">":"&gt;",'"':"&quot;","'":"&#39;"}[c]));}
async function loadSpeeches(){
  const speeches=await api("/api/speeches/");
  $("speechList").innerHTML=speeches.length?speeches.map(s=>`
    <div class="speech-row"><div><b>${escapeHtml(s.title||"Speech #"+s.id)}</b><small>${escapeHtml(s.politician_name)} · ${escapeHtml(s.location||"Location not set")} · ${escapeHtml(s.current_stage)}</small></div>
    <div><span class="status-pill">${escapeHtml(s.status)}</span> <button class="secondary" onclick="openSpeech(${s.id})">View</button></div></div>`).join(""):"<p class='muted'>No speeches yet. Add a politician in Django Admin, then submit a YouTube URL.</p>";
}
async function openSpeech(id){
  selectedSpeech=id;$("analysis").classList.remove("hidden");
  $("speechHeading").textContent="Loading speech...";
  const data=await api(`/api/dashboard/${id}/`);
  const s=data.speech;
  $("speechHeading").textContent=s.title||`Speech #${s.id}`;
  $("speechMeta").textContent=`${s.politician_name} · ${s.location||"Location not provided"} · ${s.youtube_url}`;
  $("speechStatus").textContent=s.status+" · "+s.current_stage;
  $("wordTotal").textContent=data.total_transcript_words.toLocaleString();
  $("language").textContent=(s.language||"—").toUpperCase();
  $("issueTotal").textContent=data.issue_mentions_count;
  $("duration").textContent=fmtTime(s.duration_seconds);
  drawChart("wordsChart","bar",data.top_words.map(x=>x.phrase),data.top_words.map(x=>x.frequency),"Occurrences");
  drawChart("issuesChart","doughnut",data.issues.map(x=>x.category),data.issues.map(x=>x.mentions),"Mentions");
  drawChart("bigramsChart","bar",data.bigrams.map(x=>x.phrase),data.bigrams.map(x=>x.frequency),"Occurrences");
  drawChart("trigramsChart","bar",data.trigrams.map(x=>x.phrase),data.trigrams.map(x=>x.frequency),"Occurrences");
  $("issueEvidence").innerHTML=data.issues.length?data.issues.map(x=>`<div class="issue-item"><b>${escapeHtml(x.category)}</b> · ${x.mentions} segment mentions · ${x.word_count} classified words</div>`).join(""):"<p class='muted'>No issue categories found yet. Check Ollama and reprocess the speech if needed.</p>";
  $("transcript").innerHTML=data.segments.map(x=>`<div class="segment"><span class="timestamp">${fmtTime(x.start_time)}</span>${escapeHtml(x.text)}</div>`).join("")||"<p class='muted'>Transcript is not available yet.</p>";
  $("analysis").scrollIntoView({behavior:"smooth"});
}
$("speechForm").addEventListener("submit",async e=>{
  e.preventDefault();$("formMessage").textContent="Submitting...";
  try{
    const data=await api("/api/speeches/",{method:"POST",body:JSON.stringify({
      politician:$("politicianSelect").value,youtube_url:$("youtubeUrl").value,
      title:$("speechTitle").value,location:$("speechLocation").value
    })});
    $("formMessage").textContent=`Speech #${data.id} queued. Refresh the library to see progress.`;
    $("speechForm").reset();await loadSpeeches();
  }catch(err){$("formMessage").textContent=err.message;}
});
$("refreshBtn").onclick=loadSpeeches;
$("askForm").addEventListener("submit",async e=>{
  e.preventDefault();if(!selectedSpeech)return;
  $("answer").textContent="Searching transcript and asking Ollama...";
  try{
    const data=await api(`/api/speeches/${selectedSpeech}/ask/`,{method:"POST",body:JSON.stringify({question:$("question").value})});
    $("answer").textContent=data.answer+"\n\nEvidence:\n"+data.sources.map(s=>`[${fmtTime(s.start)}–${fmtTime(s.end)}] ${s.text}`).join("\n\n");
  }catch(err){$("answer").textContent=err.message;}
});
(async()=>{try{await loadPoliticians();await loadSpeeches();}catch(e){$("speechList").textContent=e.message;}})();
